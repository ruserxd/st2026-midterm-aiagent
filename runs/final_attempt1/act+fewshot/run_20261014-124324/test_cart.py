import pytest
import cart

# Helper to format floats for comparison
def approx_equal(a,b,eps=1e-2):
    return abs(a-b) < eps

# Tests for apply_discount
@pytest.mark.parametrize("price,percent,expected",[
    (200,15,170.0),
    (100,0,100.0),
    (50,100,0.0),
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# Validation of errors for apply_discount
@pytest.mark.parametrize("price",[-1, -10])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent",[-5,101])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize("qty,expected",[
    (9,0),
    (10,5),
    (49,5),
    (50,10),
    (99,10),
    (100,15),
    (150,15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty",[0,-1,3.5,"a"])
def test_bulk_discount_invalid_qty_raises(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# parse_coupon tests
@pytest.mark.parametrize("code,expected",[
    ("SAVE10",10),
    ("save20",20),
    ("  SaVe30  ",30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code",["SAVE0","SAVEX5","NOPE","saver10","SAVE51","save-1"])
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal,member,expected",[
    (1000, False, 0),
    (999.99, False, 60),
    (0, True, 30),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal",[-1,-100])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart functionality tests
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_total_zero(self):
        assert self.cart.total() == 0.00

    def test_add_and_subtotal(self):
        self.cart.add_item("apple", unit_price=100, quantity=2)
        self.cart.add_item("banana", unit_price=50, quantity=3)
        # subtotal = 2*100 + 3*50 = 350
        assert self.cart.subtotal() == 350

    def test_remove_item(self):
        self.cart.add_item("item", unit_price=200, quantity=5)
        self.cart.remove_item("item", quantity=2)
        assert self.cart.items()["item"]["quantity"] == 3

    def test_remove_more_than_exists_raises(self):
        self.cart.add_item("x", unit_price=10, quantity=1)
        with pytest.raises(ValueError):
            self.cart.remove_item("x", quantity=2)

    def test_total_with_coupon_and_shipping(self):
        # Add items totaling 500
        self.cart.add_item("prod", unit_price=250, quantity=2)
        # Apply coupon SAVE10 -> discount 10%
        total = self.cart.total(coupon="SAVE10")
        # subtotal after coupon: 500 - 50 = 450
        # shipping fee for non-member: 60 (since <1000)
        # expected total: 450 + 60 = 510.0
        assert approx_equal(total, 510.0)

    def test_total_member_shipping_half(self):
        self.cart.add_item("p", unit_price=200, quantity=5)  # subtotal 1000
        # member should get free shipping
        total = self.cart.total(member=True)
        assert approx_equal(total, 1000.00)

    def test_total_invalid_coupon_raises(self):
        self.cart.add_item("y", unit_price=10, quantity=1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")
