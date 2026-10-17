import pytest
from cart import Cart, parse_coupon, shipping_fee, bulk_discount_percent, apply_discount

# Helper to compare floating values with rounding
def round2(x):
    return round(float(x), 2)

class TestCartSubtotal:
    def test_empty_subtotal(self):
        c = Cart()
        assert round2(c.subtotal()) == 0

    def test_single_item(self):
        c = Cart()
        c.add_item("apple", unit_price=50, quantity=3)
        # subtotal: 150
        assert round2(c.subtotal()) == 150

    def test_multiple_items_and_removal(self):
        c = Cart()
        c.add_item("banana", 20, quantity=5)   # 100
        c.add_item("orange", 30, quantity=2)   # 60
        assert round2(c.subtotal()) == 160
        c.remove_item("banana", quantity=3)    # remove 3 bananas: -60 -> subtotal 100
        assert round2(c.subtotal()) == 100
        # remove more than exists should remove all
        c.remove_item("orange")                 # default qty1
        assert round2(c.subtotal()) == 70

class TestCouponParsing:
    @pytest.mark.parametrize(
        "code,expected",
        [
            ("SAVE10", 10),
            ("save20", 20),
            ("  SaVe30  ", 30),
        ],
    )
    def test_valid_coupons(self, code, expected):
        assert parse_coupon(code) == expected

    @pytest.mark.parametrize("code", [
        "",
        "SAVE0",
        "SAVE51",
        "DISCOUNT10",
        "SAVEXX",
        None,
    ])
    def test_invalid_coupons(self, code):
        with pytest.raises(ValueError):
            parse_coupon(code)

class TestShippingFee:
    @pytest.mark.parametrize("subtotal,member,expected", [
        (0, False, 60),
        (999.99, False, 60),
        (1000, False, 0),
        (2000, False, 0),
        (500, True, 30),
    ])
    def test_shipping_fee(self, subtotal, member, expected):
        assert shipping_fee(subtotal, member) == expected

    def test_negative_subtotal_raises(self):
        with pytest.raises(ValueError):
            shipping_fee(-10)

class TestCartTotal:
    def test_total_no_coupon_non_member(self):
        c = Cart()
        c.add_item("item", 100, quantity=2)   # subtotal 200
        total = c.total(member=False)
        assert round2(total) == 260  # 200 + shipping 60

    def test_total_with_coupon_and_member(self):
        c = Cart()
        c.add_item("expensive", 600, quantity=1)
        c.add_item("cheap", 100, quantity=3)   # subtotal 1200
        # coupon SAVE10 -> 12%? Wait percent is parse_coupon returns int percent. So discount 10%
        total = c.total(member=True, coupon="SAVE10")
        # after discount: 1200 * 0.9 = 1080
        # shipping free because subtotal >=1000 -> 0
        assert round2(total) == 1080

    def test_total_rounding(self):
        c = Cart()
        c.add_item("piece", 33, quantity=3)   # 99
        total = c.total(coupon="SAVE10")
        # subtotal 99 * 0.9 = 89.1; shipping 60 -> 149.1
        assert round2(total) == 149.1

    def test_empty_cart_total(self):
        c = Cart()
        assert c.total() == 0

    def test_invalid_coupon_raises_in_total(self):
        c = Cart()
        c.add_item("item", 50)
        with pytest.raises(ValueError):
            c.total(coupon="BADCODE")

# Tests for bulk_discount_percent and apply_discount can be added if needed
