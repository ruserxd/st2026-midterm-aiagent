import pytest
import cart

# ---- utility fixtures ----
@pytest.fixture
def empty_cart():
    return cart.Cart()

# ---- tests for apply_discount ----

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 10) == 90.0
    # rounding test
    assert cart.apply_discount(99.999, 20) == round(79.9992, 2)

def test_apply_discount_errors():
    with pytest.raises(ValueError):
        cart.apply_discount(-1, 10)
    with pytest.raises(ValueError):
        cart.apply_discount(100, -5)
    with pytest.raises(ValueError):
        cart.apply_discount(100, 105)

# ---- tests for bulk_discount_percent ----

def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(200) == 15

def test_bulk_discount_percent_errors():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-5)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(3.5)

# ---- tests for parse_coupon ----

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save50") == 50
    assert cart.parse_coupon(" SAVE25 ") == 25
    # boundary values
    assert cart.parse_coupon("SAVE1") == 1
    assert cart.parse_coupon("SAVE50") == 50

def test_parse_coupon_invalid():
    with pytest.raises(ValueError):
        cart.parse_coupon("INVALID")
    with pytest.raises(ValueError):
        cart.parse_coupon("save0")   # N<1
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE51")  # N>50
    with pytest.raises(ValueError):
        cart.parse_coupon("SA VE10")

# ---- tests for shipping_fee ----

def test_shipping_fee():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0
    # member discount
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(1200, member=True) == 0

def test_shipping_fee_errors():
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

# ---- tests for Cart methods ----

def test_cart_add_and_items(empty_cart):
    c = empty_cart
    assert c.items() == {}
    c.add_item("apple", 5.0, quantity=2)
    assert c.items() == {"apple": 2}
    # adding same item increases quantity
    c.add_item("apple", 5.0, quantity=3)
    assert c.items() == {"apple": 5}
    # different item
    c.add_item("banana", 1.5)
    assert c.items() == {"apple": 5, "banana": 1}

def test_cart_add_errors(empty_cart):
    with pytest.raises(ValueError):
        empty_cart.add_item("pear", -2, quantity=1)
    with pytest.raises(ValueError):
        empty_cart.add_item("pear", 2, quantity=0)
    with pytest.raises(ValueError):
        empty_cart.add_item("pear", 2, quantity=-3)

    # mismatched unit price
    empty_cart.add_item("orange", 3.0, quantity=1)
    with pytest.raises(ValueError):
        empty_cart.add_item("orange", 4.0, quantity=1)

def test_cart_remove_and_items(empty_cart):
    c = empty_cart
    c.add_item("tshirt", 20, quantity=3)
    c.remove_item("tshirt", quantity=2)
    assert c.items() == {"tshirt": 1}
    # remove last remaining
    c.remove_item("tshirt", quantity=1)
    assert "tshirt" not in c.items()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent")

# ---- tests for Cart subtotal and total ----

def test_cart_subtotal_and_total(empty_cart):
    c = empty_cart
    # empty cart
    assert c.subtotal() == 0
    assert c.total() == 0
    # add items with bulk discount
    c.add_item("widget", 100, quantity=9)   # no bulk discount
    c.add_item("gadget", 200, quantity=10)  # 5% bulk discount
    # subtotal calculation
    widget_total = 100 * 9
    gadget_total = cart.apply_discount(200 * 10, 5)
    expected_subtotal = round(widget_total + gadget_total, 2)
    assert c.subtotal() == expected_subtotal
    # total without coupon and non-member: add shipping 60
    expected_total = round(expected_subtotal + 60, 2)
    assert c.total() == expected_total
    # with member discount on shipping
    expected_total_member = round(expected_subtotal + 30, 2)
    assert c.total(member=True) == expected_total_member
    # apply a valid coupon (SAVE10)
    subtotal_after_coupon = cart.apply_discount(expected_subtotal, 10)
    shipping = cart.shipping_fee(subtotal_after_coupon)
    total_with_coupon = round(subtotal_after_coupon + shipping, 2)
    assert c.total(coupon="SAVE10") == total_with_coupon

# ---- tests for invalid coupon in Cart.total ----

def test_cart_total_invalid_coupon(empty_cart):
    c = empty_cart
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
