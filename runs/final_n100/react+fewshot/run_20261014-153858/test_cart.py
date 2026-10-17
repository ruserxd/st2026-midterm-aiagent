import pytest
import cart

# Helper functions for expected values derived from spec

def expected_apply_discount(price, percent):
    return round(price * (1 - percent/100), 2)

def expected_bulk_discount_percent(quantity):
    if quantity >= 100:
        return 15
    if quantity >= 50:
        return 10
    if quantity >= 10:
        return 5
    return 0

# parse_coupon should return int percent

class TestApplyDiscount:
    def test_normal(self):
        assert cart.apply_discount(200, 15) == 170.0
        assert cart.apply_discount(100, 0) == 100.0
        assert cart.apply_discount(123.45, 25) == expected_apply_discount(123.45, 25)

    def test_invalid_price(self):
        with pytest.raises(ValueError):
            cart.apply_discount(-10, 5)

    def test_invalid_percent_low(self):
        with pytest.raises(ValueError):
            cart.apply_discount(100, -1)

    def test_invalid_percent_high(self):
        with pytest.raises(ValueError):
            cart.apply_discount(100, 101)

class TestBulkDiscountPercent:
    @pytest.mark.parametrize("qty,exp",[(9,0),(10,5),(49,5),(50,10),(99,10),(100,15)])
    def test_bounds(self,qty,exp):
        assert cart.bulk_discount_percent(qty) == exp

    def test_invalid_qty_zero(self):
        with pytest.raises(ValueError):
            cart.bulk_discount_percent(0)

    def test_invalid_qty_negative(self):
        with pytest.raises(ValueError):
            cart.bulk_discount_percent(-5)

class TestParseCoupon:
    @pytest.mark.parametrize("code,exp",[
        ("SAVE10",10),
        ("save25",25),
        (" SAVE50 ",50),
    ])
    def test_valid(self,code,exp):
        assert cart.parse_coupon(code) == exp

    @pytest.mark.parametrize("code",[
        "SAVE0",
        "SAVE51",
        "INVALID",
        "SAVEXY",
        " ",
    ])
    def test_invalid(self,code):
        with pytest.raises(ValueError):
            cart.parse_coupon(code)

class TestShippingFee:
    def test_free_shipping_over_limit(self):
        assert cart.shipping_fee(1000) == 0
        assert cart.shipping_fee(1500.5) == 0

    def test_regular_fee_non_member(self):
        assert cart.shipping_fee(999.99) == 60
        assert cart.shipping_fee(500) == 60

    def test_half_fee_member(self):
        assert cart.shipping_fee(800, member=True) == 30
        assert cart.shipping_fee(200, member=True) == 30

    def test_invalid_subtotal_negative(self):
        with pytest.raises(ValueError):
            cart.shipping_fee(-10)

class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_new_item(self):
        self.cart.add_item('apple', 2.5, 3)
        assert self.cart.items() == {'apple': 3}
        assert self.cart.subtotal() == 7.5

    def test_add_existing_same_price(self):
        self.cart.add_item('banana', 1.0, 2)
        self.cart.add_item('banana', 1.0, 3)
        assert self.cart.items() == {'banana': 5}
        assert self.cart.subtotal() == 5.0

    def test_add_existing_different_price(self):
        self.cart.add_item('orange', 2.0)
        with pytest.raises(ValueError):
            self.cart.add_item('orange', 3.0, 1)

    def test_remove_partial(self):
        self.cart.add_item('milk', 3.0, 5)
        self.cart.remove_item('milk', 2)
        assert self.cart.items() == {'milk': 3}
        assert self.cart.subtotal() == 9.0

    def test_remove_entire(self):
        self.cart.add_item('bread', 2.0, 4)
        self.cart.remove_item('bread', 4)
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0

    def test_remove_more_than_exists(self):
        self.cart.add_item('cheese', 5.0, 2)
        self.cart.remove_item('cheese', 5)
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0

    def test_remove_nonexistent_key(self):
        with pytest.raises(KeyError):
            self.cart.remove_item('nonexistent', 1)

    def test_total_no_discounts(self):
        self.cart.add_item('pen', 2.0, 3)  # subtotal = 6
        assert self.cart.total() == 6

    def test_total_with_shipping_and_member_discount(self):
        # Subtotal: 2000, shipping free
        for i in range(10):
            self.cart.add_item(f'item{i}', 200.0)
        assert self.cart.subtotal() == 2000
        assert self.cart.total(member=True) == 2000  # member discount applied to subtotal before shipping

    def test_total_with_coupon(self):
        self.cart.add_item('gift', 100.0, 2)  # subtotal = 200
        total = self.cart.total(coupon='SAVE20')
        # 20% off: 160 + shipping fee 60 = 220
        assert total == 220.0

    def test_total_with_coupon_and_member(self):
        self.cart.add_item('gift', 200.0, 3)  # subtotal=600
        total = self.cart.total(member=True, coupon='SAVE10')
        # 10% off: 540 + shipping fee 60 (member pays half 30) = 570
        assert total == 570.0
