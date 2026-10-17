import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# ---------- apply_discount ----------
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200.0, 15, 170.0),           # example
        (100.0, 0, 100.0),            # no discount
        (50.0, 100, 0.0),             # full discount
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price,percent",
    [(-10, 20), (50, -5), (50, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (5, 0),      # less than 10
        (10, 5),     # >=10 <50
        (49, 5),     # just below 50
        (50, 10),    # >=50 <100
        (99, 10),    # just below 100
        (100, 15),   # >=100
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -1, 3.5],  # non-positive or not int
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),          # case-insensitive
        (" SAVE30 ", 30),       # whitespace ignored
        ("Save5", 5),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    ["INVALID", "SAVE0", "SAVE51", "SAVEX", "123", ""],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (500, False, 60),     # under 1000, non-member
        (999.99, True, 30),   # under 1000, member
        (1000, False, 0),     # free
        (2000, True, 0),      # free even for members
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-1, -100.5],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class tests ----------
@pytest.fixture
def empty_cart():
    return Cart()

def test_add_item_new(empty_cart):
    cart = empty_cart
    cart.add_item("apple", 0.5, 3)
    assert cart.items() == {"apple": 3}

def test_add_item_existing_same_price(empty_cart):
    cart = empty_cart
    cart.add_item("banana", 1.0, 2)
    cart.add_item("banana", 1.0, 3)
    assert cart.items() == {"banana": 5}

def test_add_item_existing_different_price(empty_cart):
    cart = empty_cart
    cart.add_item("orange", 0.8, 2)
    with pytest.raises(ValueError):
        cart.add_item("orange", 1.0, 1)

@pytest.mark.parametrize(
    "quantity",
    [0, -5, 3.7],
)
def test_add_item_invalid_quantity(empty_cart, quantity):
    with pytest.raises(ValueError):
        empty_cart.add_item("pear", 0.6, quantity)

@pytest.mark.parametrize(
    "unit_price",
    [-1, -0.5],
)
def test_add_item_invalid_unit_price(empty_cart, unit_price):
    with pytest.raises(ValueError):
        empty_cart.add_item("melon", unit_price, 2)

def test_remove_item_partial(empty_cart):
    cart = empty_cart
    cart.add_item("cherry", 0.3, 5)
    cart.remove_item("cherry", 2)
    assert cart.items() == {"cherry": 3}

def test_remove_item_to_zero(empty_cart):
    cart = empty_cart
    cart.add_item("peach", 0.9, 4)
    cart.remove_item("peach", 4)
    assert "peach" not in cart.items()

def test_remove_item_more_than_existing(empty_cart):
    cart = empty_cart
    cart.add_item("plum", 1.2, 3)
    cart.remove_item("plum", 5)  # should remove entirely
    assert "plum" not in cart.items()

def test_remove_nonexistent(empty_cart):
    with pytest.raises(KeyError):
        empty_cart.remove_item("fig", 1)

# Subtotal tests (including bulk discounts)

def test_subtotal_single_no_discount(empty_cart):
    cart = empty_cart
    cart.add_item("itemA", 10.0, 4)  # <10 => no discount
    assert cart.subtotal() == 40.00

def test_subtotal_with_bulk_discount_5_percent(empty_cart):
    cart = empty_cart
    cart.add_item("itemB", 20.0, 12)  # >=10 <50 => 5%
    expected = round(20.0 * 12 * (1 - 0.05), 2)
    assert cart.subtotal() == expected

def test_subtotal_multiple_items(empty_cart):
    cart = empty_cart
    cart.add_item("itemC", 5.0, 8)   # no discount
    cart.add_item("itemD", 3.0, 55)  # >=50 <100 =>10%
    subtotal_c = 5.0 * 8
    subtotal_d = round(3.0 * 55 * (1 - 0.10), 2)
    assert cart.subtotal() == round(subtotal_c + subtotal_d, 2)

# Total tests with coupon and shipping

def test_total_no_coupon_no_member(empty_cart):
    cart = empty_cart
    cart.add_item("itemE", 200.0, 1)  # subtotal 200
    total = cart.total()
    # subtotal 200, no coupon => 200, shipping fee 60 => 260
    assert total == 260.00

def test_total_with_coupon_and_member(empty_cart):
    cart = empty_cart
    cart.add_item("itemF", 300.0, 2)   # subtotal 600
    # coupon SAVE10 -> 10% off subtotal => 540
    # shipping fee on 540: member pays half 30
    total = cart.total(member=True, coupon="SAVE10")
    expected_subtotal_after_coupon = round(600 * (1 - 0.10), 2)
    expected_shipping = 30 if True else 60
    expected_total = round(expected_subtotal_after_coupon + expected_shipping, 2)
    assert total == expected_total

def test_total_empty_cart(empty_cart):
    assert empty_cart.total() == 0.00

# Invalid coupon in total

def test_total_invalid_coupon(empty_cart):
    cart = empty_cart
    cart.add_item("itemG", 50.0, 1)
    with pytest.raises(ValueError):
        cart.total(coupon="BADCODE")
