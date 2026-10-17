import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount -------------------------------------
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200.0, 15, 170.0),   # example
        (100.0, 0, 100.0),     # no discount
        (50.5, 20, 40.4),      # check rounding
    ],
)
def test_apply_discount_valid(price, percent, result):
    assert apply_discount(price, percent) == result

# invalid price < 0
with pytest.raises(ValueError):
    apply_discount(-1, 10)

# invalid percent >100
with pytest.raises(ValueError):
    apply_discount(50, 150)

# invalid percent negative
with pytest.raises(ValueError):
    apply_discount(50, -5)

# ---------- bulk_discount_percent -------------------------------------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (1, 0),   # below threshold
        (9, 0),
        (10, 5),
        (19, 5),
        (50, 10),  # correct per spec
        (99, 10),
        (100, 15),
        (200, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

# non‑positive quantity raises ValueError
with pytest.raises(ValueError):
    bulk_discount_percent(0)
with pytest.raises(ValueError):
    bulk_discount_percent(-5)

# ---------- parse_coupon -------------------------------------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save25", 25),
        (" SAVE30 ", 30),
        ("SaVe1", 1),
        ("SaVe50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

# invalid format or out of bounds raise ValueError
with pytest.raises(ValueError):
    parse_coupon("SAVE0")   # below 1
with pytest.raises(ValueError):
    parse_coupon("SAVEX")  # non‑numeric suffix
with pytest.raises(ValueError):
    parse_coupon("NOPE10")
with pytest.raises(ValueError):
    parse_coupon("  ")

# ---------- shipping_fee -------------------------------------
@pytest.mark.parametrize(
    "subtotal,member,result",
    [
        (0.0, False, 60),
        (500, True, 30),
        (999.99, False, 60),
        (1000, False, 0),
        (2000, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, result):
    assert shipping_fee(subtotal, member) == result

with pytest.raises(ValueError):
    shipping_fee(-10, False)

# ---------- Cart -------------------------------------
@pytest.fixture
def cart():
    return Cart()

# add_item: basic and cumulative behavior

def test_add_item_basic(cart):
    cart.add_item("apple", 1.00, quantity=3)
    assert cart.items() == {"apple": 3}
    # unit price must be the same on subsequent adds
    cart.add_item("apple", 1.00, quantity=2)
    assert cart.items() == {"apple": 5}

# adding with different unit price raises ValueError
with pytest.raises(ValueError):
    c = Cart()
    c.add_item("banana", 0.50)
    c.add_item("banana", 0.60)

# negative or zero quantity raises ValueError
with pytest.raises(ValueError):
    c = Cart()
    c.add_item("orange", 0.30, quantity=0)

# remove_item removes correctly and deletes when qty reaches 0

def test_remove_item(cart):
    cart.add_item("pear", 0.80, quantity=4)
    cart.remove_item("pear", quantity=2)
    assert cart.items() == {"pear": 2}
    # removing remaining items removes the key
    cart.remove_item("pear", quantity=2)
    assert cart.items() == {}

# removing more than present leaves zero and deletes

def test_remove_more_than_present(cart):
    cart.add_item("kiwi", 0.90, quantity=1)
    cart.remove_item("kiwi", quantity=5)  # should remove key
    assert cart.items() == {}

# removing non‑existent item raises KeyError
with pytest.raises(KeyError):
    c = Cart()
    c.remove_item("nonexist")

# subtotal: bulk discounts applied correctly and rounding

def test_subtotal(cart):
    # 9 apples at $1 each - no discount, subtotal 9.00
    cart.add_item("apple", 1.0, quantity=9)
    assert cart.subtotal() == 9.00
    # 10 bananas at $2 each - bulk discount 5%: 20 * 0.95 = 19.0
    cart.add_item("banana", 2.0, quantity=10)
    assert cart.subtotal() == round(9.00 + 19.0, 2)  # 28.00

# empty cart subtotal is 0

def test_empty_cart_subtotal(cart):
    assert cart.subtotal() == 0

# total: coupon applied before shipping; rounding checked

def test_total_with_coupon_and_shipping(cart):
    cart.add_item("tshirt", 20.0, quantity=5)   # 5 items - no bulk discount
    subtotal = cart.subtotal()
    assert subtotal == round(20.0 * 5, 2)
    # apply coupon SAVE10 - 10% off
    total_before_shipping = round(subtotal * 0.90, 2)
    shipping = shipping_fee(total_before_shipping, member=False)  # member default False
    expected_total = round(total_before_shipping + shipping, 2)
    assert cart.total(coupon="SAVE10") == expected_total

# total with invalid coupon raises ValueError
with pytest.raises(ValueError):
    c = Cart()
    c.add_item("item", 10.0)
    c.total(coupon="INVALID")

# empty cart totals to zero, no shipping

def test_empty_cart_total(cart):
    assert cart.total() == 0

# member flag influences shipping in total calculation

def test_total_member_shipping(cart):
    cart.add_item("book", 30.0)
    subtotal = cart.subtotal()
    # no coupon
    shipping_nonmember = shipping_fee(subtotal, member=False)
    shipping_member = shipping_fee(subtotal, member=True)
    expected_nonmember = round(subtotal + shipping_nonmember, 2)
    expected_member = round(subtotal + shipping_member, 2)
    assert cart.total(member=False) == expected_nonmember
    assert cart.total(member=True) == expected_member
