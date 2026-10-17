import pytest
import cart

# Helper function to create a cart with one item

def make_cart(name="item", unit_price=100, quantity=1):
    c = cart.Cart()
    c.add_item(name, unit_price, quantity)
    return c

class TestApplyDiscount:
    def test_basic_discount(self):
        assert cart.apply_discount(200, 15) == 170.0

    def test_no_discount(self):
        assert cart.apply_discount(50, 0) == 50.0

    def test_full_discount(self):
        assert cart.apply_discount(300, 100) == 0.0

    def test_invalid_price(self):
        with pytest.raises(ValueError):
            cart.apply_discount(-10, 20)

    def test_invalid_percent_over(self):
        with pytest.raises(ValueError):
            cart.apply_discount(100, 120)

    def test_invalid_percent_under(self):
        with pytest.raises(ValueError):
            cart.apply_discount(100, -5)

class TestBulkDiscountPercent:
    @pytest.mark.parametrize(
        "quantity,expected",
        [
            (9, 0),
            (10, 5),
            (49, 5),
            (50, 10),
            (99, 10),
            (100, 15),
            (150, 15),
        ],
    )
    def test_percent(self, quantity, expected):
        assert cart.bulk_discount_percent(quantity) == expected

    def test_invalid_quantity_type(self):
        with pytest.raises(ValueError):
            cart.bulk_discount_percent("ten")

    def test_negative_quantity(self):
        with pytest.raises(ValueError):
            cart.bulk_discount_percent(-5)

class TestParseCoupon:
    @pytest.mark.parametrize(
        "code,expected",
        [
            ("SAVE10", 10),
            ("save20", 20),
            ("   SaVe30  ", 30),
        ],
    )
    def test_valid_codes(self, code, expected):
        assert cart.parse_coupon(code) == expected

    @pytest.mark.parametrize(
        "code",
        [
            "SAV10",     # missing E
            "SAVEabc",   # non-numeric
            "SAVE-5",    # negative number
            "SAVE60",    # >50
            "",          # empty string
            123,          # not a string
        ],
    )
    def test_invalid_codes(self, code):
        with pytest.raises(ValueError):
            cart.parse_coupon(code)

class TestShippingFee:
    def test_free_shipping_over_threshold(self):
        assert cart.shipping_fee(1000) == 0
        assert cart.shipping_fee(1500.75) == 0

    def test_half_for_members(self):
        assert cart.shipping_fee(500, member=True) == 30
        assert cart.shipping_fee(999.99, member=True) == 30

    def test_full_fee_non_member(self):
        assert cart.shipping_fee(300) == 60

    def test_negative_subtotal_raises(self):
        with pytest.raises(ValueError):
            cart.shipping_fee(-10)

class TestCartOperations:
    def test_add_and_items(self):
        c = make_cart()
        assert c.items() == {"item": 1}
        c.add_item("item", 100, quantity=2)
        assert c.items() == {"item": 3}

    def test_add_different_price_raises(self):
        c = cart.Cart()
        c.add_item("apple", 50)
        with pytest.raises(ValueError):
            c.add_item("apple", 60)  # price mismatch

    def test_remove_item_quantity_decrease(self):
        c = make_cart(quantity=3)
        c.remove_item("item")  # remove one default
        assert c.items() == {"item": 2}
        c.remove_item("item", quantity=2)
        assert c.items() == {}

    def test_remove_more_than_present_deletes(self):
        c = make_cart(quantity=1)
        c.remove_item("item", quantity=5)  # should delete after negative
        assert c.items() == {}

    def test_remove_nonexistent_raises_keyerror(self):
        c = cart.Cart()
        with pytest.raises(KeyError):
            c.remove_item("ghost")

    def test_subtotal_with_bulk_discount(self):
        c = cart.Cart()
        c.add_item("small", 20, quantity=5)   # no discount
        c.add_item("medium", 10, quantity=12)  # 5% bulk discount on medium only
        # small total: 20*5=100 (no discount)
        # medium total before discount: 10*12=120; discount percent 5 -> 114
        assert c.subtotal() == round(100 + 114, 2)  # 214.0

    def test_total_with_coupon_and_shipping(self):
        c = cart.Cart()
        c.add_item("book", 200, quantity=1)
        subtotal = c.subtotal()
        assert subtotal == 200
        # no coupon, non-member: shipping 60 -> total 260
        assert c.total() == round(200 + 60, 2)
        # with member discount: shipping half
        assert c.total(member=True) == round(200 + 30, 2)
        # apply valid coupon SAVE10
        assert c.total(coupon="SAVE10") == round(180 + 60, 2)
        # combined member and coupon
        assert c.total(member=True, coupon="save10") == round(180 + 30, 2)

    def test_total_empty_cart(self):
        c = cart.Cart()
        assert c.total() == 0

    def test_total_invalid_coupon_raises(self):
        c = cart.Cart()
        c.add_item("toy", 50)
        with pytest.raises(ValueError):
            c.total(coupon="BADCODE")
