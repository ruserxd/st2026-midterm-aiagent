import pytest
import cart

# helper for rounding compare

def approx(x, y, tol=1e-2):
    return abs(x - y) < tol

# ---------- apply_discount -------------------------------------------------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# boundaries for errors
@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent ----------------------------------------
@pytest.mark.parametrize("qty,expected", [
    (5, 0), (9, 0), (10, 5), (49, 5), (50, 10), (99, 10), (100, 15), (150, 15)
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

# error on non-integer or <=0
@pytest.mark.parametrize("qty", [0, -1, 3.5, "10"])
def test_bulk_discount_invalid_qty_raises(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- parse_coupon ---------------------------------------------------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10), ("save5", 5), (" SAVE50 ", 50), ("Save1",1)
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# invalid patterns
@pytest.mark.parametrize("code", ["SAV10", "SAVE0", "SAVE51", "INVALID", "",
                                   123, None])
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ---------------------------------------------------
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60), (999.99, False, 60), (1000, False, 0), (1500, True, 0),
    (200, True, 30), (500, False, 60)
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# negative subtotal error
@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class -----------------------------------------------------
@pytest.fixture
def empty_cart():
    return cart.Cart()

# adding items and subtotal calculations

def test_add_item_and_subtotal_basic(empty_cart):
    c = empty_cart
    c.add_item("apple", 1.0, 5)
    assert c.items() == {"apple":5}
    # bulk discount: quantity 5 -> 0%
    assert c.subtotal() == 5.0

# test bulk discount in subtotal

def test_subtotal_bulk_discount(empty_cart):
    c = empty_cart
    c.add_item("banana", 2.0, 12)  # qty >=10 -> 5% off
    # 2*12=24, minus 5% => 22.8
    assert approx(c.subtotal(), 22.80)

# test total with coupon and shipping

def test_total_with_coupon_and_shipping(empty_cart):
    c = empty_cart
    c.add_item("item", 500.0, 2)   # subtotal 1000 -> free shipping
    amount_before_coup = 1000.0
    # apply coupon SAVE10: reduce 10% -> 900
    expected_total = 900 + cart.shipping_fee(amount_before_coup, member=False)
    assert approx(c.total(coupon="SAVE10"), expected_total)

# test total uses subtotal after coupon for shipping? spec says yes.

def test_total_shipping_on_coupon_amount(empty_cart):
    c = empty_cart
    c.add_item("item", 100.0, 1)   # subtotal 100
    # without coupon: shipping 60 -> total 160
    assert approx(c.total(), 160.0)
    # with coupon 50% off: amount 50, shipping 30 (member True)
    assert approx(c.total(member=True, coupon="SAVE50"), 80.0)

# test remove_item logic bug: removing to zero does not delete

def test_remove_item_to_zero_not_removed(empty_cart):
    c = empty_cart
    c.add_item("foo", 10, 2)
    c.remove_item("foo", 2)
    # expected items still present with quantity 0? spec says removed when reaches 0 or less.
    assert "foo" not in c.items()

# test remove non-existing raises KeyError

def test_remove_nonexistent_raises(empty_cart):
    c = empty_cart
    with pytest.raises(KeyError):
        c.remove_item("bar")

# test add existing with different unit_price raises ValueError

def test_add_existing_different_price(empty_cart):
    c = empty_cart
    c.add_item("dup", 5.0, 1)
    with pytest.raises(ValueError):
        c.add_item("dup", 6.0, 1)

# test negative unit price or non-positive quantity raise ValueError

def test_add_invalid_price_quantity(empty_cart):
    c = empty_cart
    with pytest.raises(ValueError):
        c.add_item("bad", -1.0, 1)
    with pytest.raises(ValueError):
        c.add_item("bad", 1.0, 0)
    with pytest.raises(ValueError):
        c.add_item("bad", 1.0, -3)

# test empty cart total is zero and no shipping

def test_total_empty_cart(empty_cart):
    assert empty_cart.total() == 0
