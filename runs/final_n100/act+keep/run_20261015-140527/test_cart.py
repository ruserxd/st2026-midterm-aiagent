import cart
import pytest

# Helper for approximate equality

def approx(x, y, eps=1e-9):
    return abs(x - y) < eps

# -------------------- apply_discount tests --------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(100, 100) == 0.0
    # rounding check
    assert cart.apply_discount(10, 33) == round(10 * (1 - 0.33), 2)

@ pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [ -1, 101])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# -------------------- bulk_discount_percent tests --------------------

def test_bulk_discount_percent_ranges():
    assert cart.bulk_discount_percent(1) == 0
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(1010) == 15

@ pytest.mark.parametrize("qty", [0, -5, 3.7])
def test_bulk_discount_invalid_quantity_raises(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# -------------------- parse_coupon tests --------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save50") == 50
    assert cart.parse_coupon(" SAVE20 ") == 20

@ pytest.mark.parametrize("code", ["",
                                    "SAVEXX",
                                    "1234",
                                    "SAVE0",
                                    "SAVE51",
                                    "XYZ10",
                                    "SAVE-5",
                                    None])
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# -------------------- shipping_fee tests --------------------

def test_shipping_fee_free_and_members():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0
    # member half fee
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(1200, member=True) == 0

@ pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# -------------------- Cart tests --------------------

def test_cart_basic_operations():
    c = cart.Cart()
    assert c.items() == []
    assert c.subtotal() == 0
    # add item
    c.add_item("apple", 100, quantity=3)
    assert len(c.items()) == 1
    assert c.items()[0]["name"] == "apple"
    assert c.subtotal() == 300
    # remove part
    c.remove_item("apple", quantity=1)
    assert c.subtotal() == 200
    # remove all
    c.remove_item("apple", quantity=2)
    assert c.items() == []
    assert c.subtotal() == 0

# Coupon and shipping calculations

def test_cart_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("widget", 200, quantity=5)  # subtotal 1000
    # No coupon, member=False -> free shipping (subtotal >= 1000)
    assert c.total() == 1000.0
    # Non-member with lower subtotal and a valid coupon
    c2 = cart.Cart()
    c2.add_item("gadget", 150, quantity=3)  # subtotal 450
    total_before_shipping = cart.apply_discount(450, 20)  # 360
    shipping = cart.shipping_fee(total_before_shipping)
    expected_total = round(total_before_shipping + shipping, 2)
    assert c2.total(coupon="SAVE20") == expected_total

# Empty cart should cost zero (no shipping)

def test_cart_empty_no_shipping():
    c = cart.Cart()
    assert c.total() == 0.0

# Invalid coupon in Cart.total raises ValueError

def test_cart_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item("thing", 100)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")

# Ensure rounding to two decimals

def test_cart_rounding_two_decimals():
    c = cart.Cart()
    c.add_item("item", 333.333, quantity=1)
    # No coupon, shipping fee applied: subtotal=333.333
    shipping = cart.shipping_fee(333.333)
    total_expected = round(333.333 + shipping, 2)
    assert c.total() == total_expected
