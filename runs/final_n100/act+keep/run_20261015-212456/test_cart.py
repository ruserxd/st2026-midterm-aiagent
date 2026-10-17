import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Helper ---------------------------------------------------

def round2(x):
    return round(float(x), 2)

# ---------- apply_discount -------------------------------------------
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),
        (100, 50, 50.0),
        (0, 0, 0.0),
    ],
)
def test_apply_discount(price, percent, result):
    assert apply_discount(price, percent) == pytest.approx(result, rel=1e-9)

# Invalid cases
@pytest.mark.parametrize("price,percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent ------------------------------------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (5, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

# Invalid quantity
@pytest.mark.parametrize("quantity", [0, -3, 1.5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon ---------------------------------------------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        ("SAVE30", 30),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVEX10", "NOPE", "save51", "1234"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ---------------------------------------------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (999.99, False, 60),
        (1000, False, 0),
        (1500, True, 0),
        (500, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

# Invalid subtotal
@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart integration ------------------------------------------
@pytest.fixture
def empty_cart():
    return Cart()

@pytest.fixture
def sample_cart():
    c = Cart()
    # 5 of A ($100 each) and 1 of B ($50)
    c.add_item("A", 100.0, quantity=5)
    c.add_item("B", 50.0, quantity=1)
    return c

# Test subtotal calculation
def test_subtotal_empty(empty_cart):
    assert empty_cart.subtotal() == pytest.approx(0)

def test_subtotal_sample(sample_cart):
    assert sample_cart.subtotal() == pytest.approx(550.0)

# Test total without coupon/member
def test_total_no_discount(sample_cart):
    assert sample_cart.total() == 610.0

# Test total with member shipping discount
def test_total_member_shipping(sample_cart):
    assert sample_cart.total(member=True) == 580.0

# Test total with coupon
@pytest.mark.parametrize(
    "coupon,expected",
    [
        ("SAVE10", 555.0),   # subtotal after discount 495 + shipping 60
    ],
)
def test_total_with_coupon(sample_cart, coupon, expected):
    assert sample_cart.total(coupon=coupon) == expected

# Test total with member and coupon
@pytest.mark.parametrize(
    "coupon,expected",
    [
        ("SAVE10", 525.0), # subtotal after discount 495 + shipping 30
    ],
)
def test_total_member_coupon(sample_cart, coupon, expected):
    assert sample_cart.total(member=True, coupon=coupon) == expected

# Test invalid coupon raises ValueError
def test_total_invalid_coupon(sample_cart):
    with pytest.raises(ValueError):
        sample_cart.total(coupon="BADCODE")

# Test remove_item functionality via subtotal changes
def test_remove_item(sample_cart):
    c = sample_cart
    # initial subtotal 550
    assert c.subtotal() == pytest.approx(550.0)
    # Remove 2 of A (price 100 each) -> subtract 200
    c.remove_item("A", quantity=2)
    assert c.subtotal() == pytest.approx(350.0)
    # Remove remaining A (3 units) and B (1 unit)
    c.remove_item("A")
    c.remove_item("B")
    assert c.subtotal() == pytest.approx(0.0)
