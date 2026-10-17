import pytest
import cart

def round2(value):
    return round(float(value), 2)

class TestFunctions:
    def test_apply_discount_valid(self):
        assert cart.apply_discount(200, 15) == 170.0
        assert cart.apply_discount(100, 0) == 100.0
        assert cart.apply_discount(100, 100) == 0.0

    def test_apply_discount_invalid(self):
        with pytest.raises(ValueError):
            cart.apply_discount(-10, 20)
        with pytest.raises(ValueError):
            cart.apply_discount(50, -5)
        with pytest.raises(ValueError):
            cart.apply_discount(50, 105)

    def test_parse_coupon_valid(self):
        assert cart.parse_coupon("SAVE10") == 10
        # whitespace and case-insensitive should be accepted as per spec
        assert cart.parse_coupon(" save20 ") == 20
        assert cart.parse_coupon("SaVe5") == 5

    def test_parse_coupon_invalid(self):
        for bad in ["SAVEX", "save0", "save51", "10", "SAVE-1"]:
            with pytest.raises(ValueError):
                cart.parse_coupon(bad)

    def test_bulk_discount_percent(self):
        assert cart.bulk_discount_percent(5) == 0
        assert cart.bulk_discount_percent(10) == 5
        assert cart.bulk_discount_percent(50) == 10
        assert cart.bulk_discount_percent(100) == 15
        with pytest.raises(ValueError):
            cart.bulk_discount_percent(-1)
        with pytest.raises(ValueError):
            cart.bulk_discount_percent(0.5)

    def test_shipping_fee(self):
        assert cart.shipping_fee(999) == 60
        assert cart.shipping_fee(1000) == 0
        assert cart.shipping_fee(500, member=True) == 30
        with pytest.raises(ValueError):
            cart.shipping_fee(-5)

class TestCart:
    def test_empty_cart_total(self):
        c = cart.Cart()
        assert c.total() == 0

    def test_add_and_remove_item(self):
        c = cart.Cart()
        c.add_item("apple", 1.0, 3)
        assert c.items() == {"apple": 3}
        c.add_item("apple", 1.0, 2)
        assert c.items() == {"apple": 5}
        with pytest.raises(ValueError):
            c.add_item("apple", 1.5, 1)

    def test_remove_more_than_quantity(self):
        c = cart.Cart()
        c.add_item("banana", 0.5, 2)
        c.remove_item("banana", 3)
        assert "banana" not in c.items()

    def test_subtotal_with_bulk_discount(self):
        c = cart.Cart()
        c.add_item("widget", 10.0, 9)
        assert round(c.subtotal(), 2) == 90.0
        c.remove_item("widget")
        c.add_item("widget", 10.0, 42)
        # Total qty now 50 -> bulk discount 15%
        expected = round(10 * 50 * 0.85, 2)
        assert round(c.subtotal(), 2) == expected

    def test_total_with_coupon_and_shipping(self):
        c = cart.Cart()
        c.add_item("item", 200.0, 5)  # subtotal 1000
        amount_before_coup = c.subtotal()
        assert amount_before_coup == 1000
        total_with_coupon = c.total(coupon="SAVE10")
        expected_discounted = round(amount_before_coup * 0.90, 2)
        expected_shipping = cart.shipping_fee(expected_discounted, member=False)
        assert total_with_coupon == round(expected_discounted + expected_shipping, 2)

    def test_total_membership_and_free_shipping(self):
        c = cart.Cart()
        c.add_item("item", 200.0, 6)  # subtotal 1200 -> free shipping
        total_no_coup = c.total(member=True)
        assert total_no_coup == round(1200 + 0, 2)
        total_with_coup = c.total(member=True, coupon="SAVE20")
        expected_discounted = round(1200 * 0.80, 2)
        assert total_with_coup == round(expected_discounted + cart.shipping_fee(c.subtotal(), member=True), 2)

    def test_total_shipping_bug_exposure(self):
        c = cart.Cart()
        c.add_item("expensive", 1000.0, 1)  # subtotal 1000 -> free shipping
        assert c.total(coupon="SAVE50") == round(500.0 + 0, 2)
        c = cart.Cart()
        c.add_item("item", 200.0, 3)   # subtotal 600
        total_with_coupon = c.total(coupon="SAVE10")
        expected_discounted = round(600 * 0.90, 2)
        shipping_on_discount = cart.shipping_fee(expected_discounted, member=False)
        assert total_with_coupon == round(expected_discounted + shipping_on_discount, 2)
