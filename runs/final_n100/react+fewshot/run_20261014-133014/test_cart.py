import pytest
import cart

# Helper: round to two decimals where needed

def _round(val):
    return round(val, 2)

# ---------- apply_discount ---------------------------------

test_apply = [
    (200, 15, 170.0),   # example from spec
    (100, 0, 100.0),     # no discount
    (50, 100, 0.0),      # full price discounted to zero
]
@pytest.mark.parametrize("price,percent,expected", test_apply)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == _round(expected)

# boundary conditions for percent and price
with pytest.raises(ValueError):
    cart.apply_discount(-1, 10)
with pytest.raises(ValueError):
    cart.apply_discount(10, -5)
with pytest.raises(ValueError):
    cart.apply_discount(10, 105)

# ---------- bulk_discount_percent ---------------------------------
bulk_cases = [
    (9, 0),   # below threshold
    (10, 5),  # first tier
    (49, 5),  # upper bound of tier 1
    (50, 10), # start of tier 2
    (99, 10), # upper bound tier 2
    (100, 15),# start of tier 3
    (250, 15) # above threshold
]
@pytest.mark.parametrize("qty,expected", bulk_cases)
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

with pytest.raises(ValueError):
    cart.bulk_discount_percent(0)
with pytest.raises(ValueError):
    cart.bulk_discount_percent(-5)

# ---------- parse_coupon ---------------------------------
valid_coupons = [
    ("SAVE10", 10),
    ("save25 ", 25),
    ("   SaVe50", 50),
    ("sAvE1", 1)
]
@pytest.mark.parametrize("code,expected", valid_coupons)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

invalid_codes = [
    "SAVE0",      # below 1
    "SAVE51",     # above 50
    "DISCOUNT10",
    "SA VE10",
    "", 
    None
]
@pytest.mark.parametrize("code", invalid_codes)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ---------------------------------
shipping_cases = [
    (0, False, 60),   # below free threshold, non‑member
    (999.99, True, 30),# just under threshold, member half
    (1000, False, 0), # exactly at threshold, free shipping
    (1500, True, 0)   # above threshold, still free
]
@pytest.mark.parametrize("subtotal,member,expected", shipping_cases)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

with pytest.raises(ValueError):
    cart.shipping_fee(-10)

# ---------- Cart class ---------------------------------

def make_cart():
    c = cart.Cart()
    c.add_item("apple", 2.5, 3)
    c.add_item("banana", 1.0, 5)
    return c

def test_add_and_items():
    c = cart.Cart()
    c.add_item("orange", 0.75)
    assert c.items() == {"orange": 1}
    # adding again increases quantity
    c.add_item("orange", 0.75, 2)
    assert c.items() == {"orange": 3}
    # unit price must match existing price
    with pytest.raises(ValueError):
        c.add_item("orange", 1.0)
    # invalid unit price or quantity
    with pytest.raises(ValueError):
        c.add_item("pear", -1, 1)
    with pytest.raises(ValueError):
        c.add_item("pear", 1, 0)

def test_remove_and_items():
    c = cart.Cart()
    c.add_item("mango", 3.0, 4)
    assert c.items() == {"mango": 4}
    # remove part of quantity
    c.remove_item("mango", 2)
    assert c.items() == {"mango": 2}
    # removing all removes key
    c.remove_item("mango", 2)
    assert c.items() == {}
    # removing more than present raises KeyError via empty cart
    with pytest.raises(KeyError):
        c.remove_item("mango", 1)

def test_subtotal():
    c = make_cart()
    # apple: qty=3, bulk discount 0% => 7.5
    # banana: qty=5, bulk discount 0% => 5.0
    assert c.subtotal() == _round(12.5)

    # test bulk discount effect
    d = cart.Cart()
    d.add_item("widget", 10, 10)   # 10 items -> 5% discount
    expected_sub = _round(10 * 10 * (1 - 0.05))
    assert d.subtotal() == expected_sub

def test_total_no_coupon_no_member():
    c = make_cart()
    subtotal = c.subtotal()
    # no coupon, non‑member shipping fee 60
    total_expected = _round(subtotal + 60)
    assert c.total() == total_expected

def test_total_with_coupon_and_member():
    c = cart.Cart()
    c.add_item("item", 100, 1)   # subtotal 100
    coupon_percent = cart.parse_coupon("SAVE20")  # 20% discount
    subtotal_after_coupon = _round(100 * (1 - coupon_percent/100))
    shipping = cart.shipping_fee(subtotal_after_coupon, member=True)
    total_expected = _round(subtotal_after_coupon + shipping)
    assert c.total(member=True, coupon="SAVE20") == total_expected

# empty cart costs 0
assert cart.Cart().total() == 0.0
