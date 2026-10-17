import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------------------------------------------------------------------------
# Helper: round two decimals
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200.0, 15, 170.0),          # example from docstring
        (100.0, 0, 100.0),           # no discount
        (50.0, 100, 0.0),            # full free
        (123.45, 7.5, 114.33),      # decimal percent
    ],
)
def test_apply_discount(price, percent, expected):
    assert apply_discount(price, percent) == pytest.approx(expected, rel=1e-9)

@pytest.mark.parametrize("price", [-10, -0.01])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        apply_discount(price, 20)

@pytest.mark.parametrize(
    "percent",
    [-5, 101, 200],
)
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------------------------------------------------------------------------
# bulk_discount_percent tests
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (9, 0),   # below 10
        (10, 5),  # exactly 10
        (49, 5),  # just below 50
        (50, 10),
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_invalid_quantity_raises(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------------------------------------------------------------------------
# parse_coupon tests
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save10", 10),
        (" SAVE20 ", 20),
        ("sAvE50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    ["SAVE0", "SAVE51", "SAVe10", "DISCOUNT10", "", "1234", None],
)
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------------------------------------------------------------------------
# shipping_fee tests
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (999.99, False, 60),   # below free threshold
        (1000, False, 0),      # exact threshold
        (1200, True, 30),      # member pays half
        (50, True, 30),        # member with low subtotal
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -0.01])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------------------------------------------------------------------------
# Cart class tests
# ---------------------------------------------------------------------------
@pytest.fixture
def cart():
    return Cart()

# Test add_item basic functionality and validation

def test_add_and_items(cart):
    cart.add_item("apple", 1.0, quantity=3)
    cart.add_item("banana", 2.5)
    assert cart.items() == {"apple": 3, "banana": 1}

# Adding existing item increases quantity and checks price consistency

def test_add_existing_same_price(cart):
    cart.add_item("apple", 1.0, quantity=2)
    cart.add_item("apple", 1.0, quantity=5)
    assert cart.items()["apple"] == 7

# Adding existing item with different price raises ValueError

def test_add_existing_different_price_raises(cart):
    cart.add_item("orange", 3.0)
    with pytest.raises(ValueError):
        cart.add_item("orange", 4.0, quantity=1)

# Validation for negative or zero price / quantity

def test_add_invalid_values(cart):
    with pytest.raises(ValueError):
        cart.add_item("negprice", -5.0)
    with pytest.raises(ValueError):
        cart.add_item("zeroprice", 0.0, quantity=0)
    with pytest.raises(ValueError):
        cart.add_item("zeroqty", 1.0, quantity=0)

# Remove item tests

def test_remove_item(cart):
    cart.add_item("pear", 2.0, quantity=5)
    cart.remove_item("pear", quantity=3)
    assert cart.items()["pear"] == 2
    # removing more than remaining should remove completely
    cart.remove_item("pear", quantity=5)
    assert "pear" not in cart.items()

def test_remove_nonexistent_raises(cart):
    with pytest.raises(KeyError):
        cart.remove_item("nonexistent")

# Subtotal calculation with bulk discount and rounding

def test_subtotal_bulk_discount(cart):
    # 12 apples at $10 each -> bulk discount 5%
    cart.add_item("apple", 10.0, quantity=12)
    expected = apply_discount(120.0, 5)  # 114.0
    assert cart.subtotal() == pytest.approx(expected, rel=1e-9)

# Empty cart subtotal is zero

def test_empty_cart_subtotal(cart):
    assert cart.subtotal() == 0

# Total with coupon and shipping logic

def test_total_no_coupon_member(cart):
    # 2 items worth $200 each, no discount => subtotal 400
    cart.add_item("item1", 200.0, quantity=2)
    total = cart.total(member=True)  # member gets half shipping if any
    # Subtotal after coupon: 400
    # Shipping fee: 60 (subtotal<1000), member half =>30
    # Total should be 430 rounded
    assert total == pytest.approx(430.0, rel=1e-9)


def test_total_with_coupon(cart):
    cart.add_item("expensive", 500.0, quantity=3)  # subtotal 1500 free shipping
    total = cart.total(coupon="SAVE10")
    # Subtotal 1500 -> coupon 10% => 1350
    # Shipping fee 0 (subtotal>=1000)
    assert total == pytest.approx(1350.0, rel=1e-9)

# Total on empty cart is zero and no shipping charged

def test_total_empty_cart(cart):
    assert cart.total() == 0

# Invalid coupon raises ValueError during total calculation

def test_total_invalid_coupon_raises(cart):
    cart.add_item("test", 100.0)
    with pytest.raises(ValueError):
        cart.total(coupon="BADCODE")

# Ensure rounding to two decimals on subtotal and total

def test_rounding_behavior(cart):
    cart.add_item("precise", 10.3333, quantity=3)  # 30.9999
    expected_subtotal = apply_discount(30.9999, 0)
    assert cart.subtotal() == pytest.approx(round(expected_subtotal, 2))
    total = cart.total()
    assert total == pytest.approx(round(cart.subtotal(), 2))
