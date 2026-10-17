import pytest
import cart

# Helper to create a cart with items

def make_cart(items):
    c = cart.Cart()
    for name, unit_price, quantity in items:
        c.add_item(name, unit_price, quantity)
    return c

class TestApplyDiscount:
    def test_basic(self):
        assert cart.apply_discount(200, 15) == 170.0
        # rounding
        assert cart.apply_discount(99.995, 10) == round(89.9955, 2)

    def test_errors(self):
        with pytest.raises(ValueError):
            cart.apply_discount(-1, 10)
        with pytest.raises(ValueError):
            cart.apply_discount(100, -5)
        with pytest.raises(ValueError):
            cart.apply_discount(100, 105)

class TestBulkDiscountPercent:
    def test_thresholds(self):
        assert cart.bulk_discount_percent(9) == 0
        assert cart.bulk_discount_percent(10) == 5
        assert cart.bulk_discount_percent(49) == 5
        assert cart.bulk_discount_percent(50) == 10
        assert cart.bulk_discount_percent(99) == 10
        assert cart.bulk_discount_percent(100) == 15
        assert cart.bulk_discount_percent(150) == 15

    def test_errors(self):
        with pytest.raises(ValueError):
            cart.bulk_discount_percent(0)
        with pytest.raises(ValueError):
            cart.bulk_discount_percent(-5)

class TestParseCoupon:
    @pytest.mark.parametrize(
        "code,expected",
        [
            ("SAVE10", 10),
            ("save20", 20),
            ("  SaVe30  ", 30),
        ],
    )
    def test_valid(self, code, expected):
        assert cart.parse_coupon(code) == expected

    @pytest.mark.parametrize("invalid", ["SAVE0", "SAVE51", "ABC10", "SAVEXX", " SAVE -5 "])
    def test_invalid(self, invalid):
        with pytest.raises(ValueError):
            cart.parse_coupon(invalid)

class TestShippingFee:
    def test_fee(self):
        assert cart.shipping_fee(999) == 60
        assert cart.shipping_fee(1000) == 0
        assert cart.shipping_fee(1500) == 0

    def test_member(self):
        assert cart.shipping_fee(500, member=True) == 30
        assert cart.shipping_fee(1200, member=True) == 0

    def test_errors(self):
        with pytest.raises(ValueError):
            cart.shipping_fee(-10)

class TestCart:
    def test_add_and_items(self):
        c = cart.Cart()
        c.add_item("apple", 2.5, 3)
        c.add_item("banana", 1.0)
        assert set(c.items().keys()) == {"apple", "banana"}
        assert c.items()["apple"] == (2.5, 3)
        assert c.items()["banana"] == (1.0, 1)

    def test_remove(self):
        c = cart.Cart()
        c.add_item("cherry", 0.5, 10)
        c.remove_item("cherry", 4)
        assert c.items()["cherry"] == (0.5, 6)
        # remove more than exists - should leave zero quantity or remove entry
        c.remove_item("cherry", 10)
        assert "cherry" not in c.items()

    def test_subtotal(self):
        c = make_cart([
            ("bread", 3.0, 2),
            ("milk", 1.5, 4),
        ])
        # 2*3 + 4*1.5 = 6 + 6 = 12
        assert c.subtotal() == 12

    def test_total(self):
        c = make_cart([
            ("item", 10, 120),   # triggers bulk discount 15%
        ])
        subtotal = c.subtotal()
        assert subtotal == 1200
        total_without_coupons = c.total(member=False)
        expected_total = cart.apply_discount(subtotal, cart.bulk_discount_percent(120))
        assert total_without_coupons == expected_total

    def test_total_with_member_and_coupon(self):
        c = make_cart([
            ("item", 20, 60),   # bulk discount 10%
        ])
        subtotal = c.subtotal()  # 1200
        total = c.total(member=True, coupon="SAVE5")
        assert total == cart.apply_discount(1080, 5)

    def test_total_edge_cases(self):
        c = cart.Cart()
        assert c.total() == 0
        c.add_item("pen", 1.0, 500)  # subtotal 500
        total = c.total(member=True)
        assert total == 530
