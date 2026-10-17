import pytest
import cart

# --- apply_discount tests ---
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),   # example from spec
    (100, 0, 100.0),    # no discount
    (50, 100, 0.0),     # full price
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# Edge cases for input validation
@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101, 200])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# --- bulk_discount_percent tests ---
@pytest.mark.parametrize("qty,expected", [
    (9, 0),     # below 10
    (10, 5),    # boundary
    (49, 5),    # just below 50
    (50, 10),   # boundary
    (99, 10),   # just below 100
    (100, 15),  # boundary
    (150, 15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

# Validation of quantity
@pytest.mark.parametrize("qty", [0, -1, 2.5])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# --- parse_coupon tests ---
valid_codes = {
    "SAVE10": 10,
    "save20": 20,
    "  SaVe30  ": 30,
}
for code, percent in valid_codes.items():
    assert cart.parse_coupon(code) == percent

invalid_codes = ["", "ABC10", "SAVEX", "SAVE0", "SAVE51", "save-5", "  SAVE50  EXTRA"]
for code in invalid_codes:
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee tests ---
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (999.99, False, 60),
    (1000, False, 0),
    (1500, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

with pytest.raises(ValueError):
    cart.shipping_fee(-10)

# --- Cart tests ---
@pytest.fixture
def empty_cart():
    return cart.Cart()

@pytest.fixture
def populated_cart(empty_cart):
    c = empty_cart
    c.add_item("apple", 1.0, 5)   # no bulk discount
    c.add_item("banana", 2.0, 12) # 5% bulk discount on bananas
    return c

# add_item behavior and validation
def test_add_item_new(empty_cart):
    empty_cart.add_item("widget", 10.0)
    assert empty_cart.items() == {"widget": 1}

def test_add_item_increase_quantity(populated_cart):
    populated_cart.add_item("apple", 1.0, 3)
    assert populated_cart.items()["apple"] == 8

def test_add_item_price_mismatch(populated_cart):
    with pytest.raises(ValueError):
        populated_cart.add_item("apple", 2.0)

# remove_item behavior
def test_remove_item_partial(populated_cart):
    populated_cart.remove_item("banana", 5)
    assert populated_cart.items()["banana"] == 7

def test_remove_item_complete(populated_cart):
    populated_cart.remove_item("apple", 5)
    assert "apple" not in populated_cart.items()

def test_remove_nonexistent(empty_cart):
    with pytest.raises(KeyError):
        empty_cart.remove_item("nonexistent")

# items returns a copy
def test_items_copy(populated_cart):
    it = populated_cart.items()
    it["apple"] = 999
    assert populated_cart.items()["apple"] == 8  # unchanged

# subtotal calculation with bulk discounts
def test_subtotal(populated_cart):
    # apple: 5 * 1.0 = 5.00, no discount
    # banana: 12 * 2.0 = 24.00, 5% discount -> 22.80
    assert populated_cart.subtotal() == pytest.approx(27.8)

# total with and without coupon/membership
def test_total_no_coupon(empty_cart):
    empty_cart.add_item("item", 50.0, 1)
    # subtotal 50, no discount, shipping 60 -> 110
    assert empty_cart.total() == pytest.approx(110.0)

def test_total_with_coupon_and_member(populated_cart):
    # subtotal computed earlier: 27.80
    # coupon SAVE10 => 27.80 * 0.9 = 24.92
    # shipping for members on 24.92 < 1000 => 30% of 60 = 30? actually member pays half fee -> 30
    # total = 24.92 + 30 = 54.92 rounded 2 decimals
    assert populated_cart.total(member=True, coupon="SAVE10") == pytest.approx(54.92)

# empty cart costs zero
empty_total = cart.Cart().total()
assert empty_total == 0.0
