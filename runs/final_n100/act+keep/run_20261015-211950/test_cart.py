import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount ---------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize(
    "price, percent",
    [(-1, 10), (100, -5), (100, 105)],
)
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent -----------------------------

def test_bulk_discount_percent_levels():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon -------------------------------------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20 ") == 20
    assert parse_coupon(" SAVE5 ") == 5

@ pytest.mark.parametrize(
    "code",
    ["", "SAVEX", "SAVE51", "SAVE0", "12345", "S AVE10"],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee -------------------------------------

def test_shipping_fee():
    assert shipping_fee(0) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500) == 0

@ pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart basic operations -----------------------------

def test_cart_add_and_items():
    c = Cart()
    assert c.items() == {}
    c.add_item("apple", 1.0, 3)
    assert c.items() == {"apple": 3}
    # Adding same item increases quantity
    c.add_item("apple", 1.0, 2)
    assert c.items() == {"apple": 5}
    # Different item
    c.add_item("banana", 0.5, 10)
    assert set(c.items().keys()) == {"apple", "banana"}

@ pytest.mark.parametrize(
    "existing_price,new_price",
    [(1.0, 2.0), (0, -1)],
)
def test_cart_add_item_invalid_price(existing_price, new_price):
    c = Cart()
    c.add_item("orange", existing_price, 1)
    with pytest.raises(ValueError):
        c.add_item("orange", new_price, 1)

@ pytest.mark.parametrize(
    "quantity",
    [0, -2, 3.5],
)
def test_cart_add_item_invalid_quantity(quantity):
    c = Cart()
    with pytest.raises(ValueError):
        c.add_item("orange", 1.0, quantity)

# ---------- remove_item --------------------------------------

def test_remove_item_basic():
    c = Cart()
    c.add_item("pear", 2.0, 4)
    c.remove_item("pear", 2)
    assert c.items() == {"pear": 2}
    # Remove remaining
    c.remove_item("pear", 2)
    assert c.items() == {}

@ pytest.mark.parametrize(
    "name",
    ["unknown"],
)
def test_remove_item_not_in_cart(name):
    c = Cart()
    with pytest.raises(KeyError):
        c.remove_item(name, 1)

# ---------- subtotal calculation ------------------------------

def test_subtotal_with_discounts():
    c = Cart()
    # No items -> 0
    assert c.subtotal() == 0
    # Add item below discount threshold
    c.add_item("itemA", 10.0, 9)
    assert c.subtotal() == pytest.approx(90.0)
    # Bulk discount applies for quantity >=10
    c.remove_item("itemA", 9)
    c.add_item("itemA", 10.0, 10)
    assert c.subtotal() == pytest.approx(95.0)  # 5% off: 100 * .95
    # Bulk discount for >=50
    c.remove_item("itemA", 10)
    c.add_item("itemA", 20.0, 50)
    assert c.subtotal() == pytest.approx(950.0)  # 10% off: 1000 * .9
    # Bulk discount for >=100
    c.remove_item("itemA", 50)
    c.add_item("itemA", 30.0, 120)
    assert c.subtotal() == pytest.approx(3240.0)  # 15% off: 3600 * .85

# ---------- total calculation ---------------------------------

def test_total_without_coupon_or_membership():
    c = Cart()
    c.add_item("item", 10.0, 1)
    assert c.total() == pytest.approx(70.0)  # 60 shipping

@ pytest.mark.parametrize(
    "member",
    [True, False],
)
def test_total_shipping_member(member):
    c = Cart()
    c.add_item("item", 200.0, 1)
    subtotal = 200.0
    shipping_expected = 30 if member else 60
    assert c.total(member=member) == pytest.approx(subtotal + shipping_expected)

@ pytest.mark.parametrize(
    "coupon_code,expected_after_coupon",
    [("SAVE10", 90.0), ("SAVE20", 80.0)],
)
def test_total_with_coupon(coupon_code, expected_after_coupon):
    c = Cart()
    c.add_item("item", 100.0, 1)
    subtotal = 100.0
    # apply coupon percent
    after_coupon = subtotal * (1 - parse_coupon(coupon_code)/100)
    shipping_expected = shipping_fee(after_coupon)
    expected_total = round(after_coupon + shipping_expected, 2)
    assert c.total(coupon=coupon_code) == pytest.approx(expected_total)

# ---------- total with empty cart ----------------------------

def test_total_empty_cart():
    c = Cart()
    assert c.total() == 0
