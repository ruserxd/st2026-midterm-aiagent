import pytest
import cart

# --- apply_discount ---------------------------------------------------
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),          # example from spec
        (100, 0, 100.0),           # no discount
        (50, 100, 0.0),            # full discount
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# invalid price or percent should raise ValueError
@pytest.mark.parametrize(
    "price, percent",
    [(-1, 10), (50, -5), (50, 105)],
)
def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --- bulk_discount_percent -------------------------------------------
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (5, 0),
        (10, 5),
        (25, 5),
        (50, 10),
        (75, 10),
        (100, 15),
        (200, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# non‑positive or non‑int quantities raise ValueError
@pytest.mark.parametrize(
    "quantity",
    [0, -3, 2.5],
)
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --- parse_coupon -----------------------------------------------------
valid_codes = {
    "SAVE10": 10,
    "save20": 20,
    "  SaVe30  ": 30,
}
@pytest.mark.parametrize("code,expected", list(valid_codes.items()))
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

invalid_codes = ["SAV5", "SAVE51", "NOPE", "", " SAVE 10"]
@pytest.mark.parametrize("code", invalid_codes)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee -----------------------------------------------------
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, 60),   # below threshold
        (500, True, 30),  # member pays half
        (1000, False, 0), # free shipping
        (1500, True, 0),  # still free
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

with pytest.raises(ValueError):
    cart.shipping_fee(-10)

# --- Cart class -------------------------------------------------------
@pytest.fixture
def empty_cart():
    return cart.Cart()

# Adding items updates quantity and keeps unit price

def test_add_item_basic(empty_cart):
    empty_cart.add_item("apple", 2.0, 3)
    assert empty_cart.items() == {"apple": 3}

# adding same item increases quantity only if unit_price matches

def test_add_same_item_increases_quantity(empty_cart):
    empty_cart.add_item("banana", 1.5, 2)
    empty_cart.add_item("banana", 1.5, 4)
    assert empty_cart.items() == {"banana": 6}

# adding same item with different price raises ValueError

def test_add_same_item_different_price(empty_cart):
    empty_cart.add_item("orange", 0.9, 1)
    with pytest.raises(ValueError):
        empty_cart.add_item("orange", 1.0, 2)

# removing items decreases quantity or removes item completely

def test_remove_item(empty_cart):
    empty_cart.add_item("cherry", 3.0, 5)
    empty_cart.remove_item("cherry", 2)
    assert empty_cart.items() == {"cherry": 3}
    empty_cart.remove_item("cherry", 3)
    assert empty_cart.items() == {}

# removing non‑existent item raises KeyError

def test_remove_nonexistent(empty_cart):
    with pytest.raises(KeyError):
        empty_cart.remove_item("pear")

# subtotal calculation with bulk discounts and rounding

def test_subtotal_with_bulk_discount_and_rounding():
    c = cart.Cart()
    # 12 apples: bulk discount 5% -> price after discount per apple = 1.0 * 0.95 = 0.95
    c.add_item("apple", 1.0, 12)
    # 60 bananas: bulk discount 10% -> 0.5 * 0.9 = 0.45 each
    c.add_item("banana", 0.5, 60)
    expected_subtotal = round(12 * 0.95 + 60 * 0.45, 2)
    assert c.subtotal() == expected_subtotal

# total with coupon and shipping fee (non‑member)

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    # items totaling exactly 1000 before discount to trigger free shipping
    c.add_item("item", 500.0, 2)  # no bulk discount applied
    subtotal = c.subtotal()  # should be 1000.0
    assert subtotal == 1000.0
    # Apply a coupon of 10% -> 900
    total = c.total(member=False, coupon="SAVE10")
    # Shipping after coupon: subtotal 900 < 1000 -> fee 60
    expected_total = round(900 + 60, 2)
    assert total == expected_total

# total with member discount and no shipping if threshold met

def test_total_member_free_shipping():
    c = cart.Cart()
    c.add_item("big", 500.0, 3)   # subtotal 1500 - free shipping
    total = c.total(member=True)
    assert total == round(1500, 2)

# invalid coupon raises ValueError during total calculation

def test_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("toy", 10.0, 1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# empty cart costs 0 and no shipping

def test_empty_cart_total_zero():
    c = cart.Cart()
    assert c.total() == 0
