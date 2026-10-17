import pytest
from cart import (
    parse_coupon,
    shipping_fee,
    bulk_discount_percent,
    apply_discount,
    Cart,
)

# ---------- parse_coupon tests ----------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        (" SaVe30 ", 30),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize(
    "invalid_code",
    ["SAVE0", "save51", "discount10", "SAVEXX", ""],
)
def test_parse_coupon_invalid(invalid_code):
    with pytest.raises(ValueError):
        parse_discount = parse_coupon  # alias to suppress flake8 unused
        parse_discount(invalid_code)

# ---------- shipping_fee tests ----------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (50, True, 30),
        (999.99, False, 60),
        (1000, False, 0),
        (1200, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-1, -100],
)
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- bulk_discount_percent tests ----------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (5, 0),
        (10, 5),
        (55, 10),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -1, 2.5],
)
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- apply_discount tests ----------
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
    ],
)
def test_apply_discount(price, percent, expected):
    assert apply_discount(price, percent) == pytest.approx(expected, rel=1e-9)

@pytest.mark.parametrize(
    "price,percent",
    [(-10, 5), (50, -1), (50, 101)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- Cart class tests ----------
@pytest.fixture
def cart():
    return Cart()

def test_add_and_items(cart):
    cart.add_item("apple", 100, quantity=2)
    assert cart.items() == {"apple": (200, 2)}

def test_remove_item(cart):
    cart.add_item("banana", 150, quantity=3)
    cart.remove_item("banana", quantity=1)
    assert cart.items() == {"banana": (150, 2)}
    # Removing more than present removes the item entirely
    cart.remove_item("banana", quantity=5)
    assert "banana" not in cart.items()

def test_subtotal(cart):
    cart.add_item("item1", 100, quantity=3)  # 300
    cart.add_item("item2", 200, quantity=1)  # 200
    assert cart.subtotal() == 500

# Cart total without coupon or member

def test_total_basic(cart):
    cart.add_item("x", 400)
    # subtotal 400 <1000 -> shipping 60
    assert cart.total(member=False, coupon=None) == 460.0

# With member discount

def test_total_member(cart):
    cart.add_item("y", 500)
    # shipping for member half
    assert cart.total(member=True, coupon=None) == 530.0

# With coupon only

def test_total_coupon(cart):
    cart.add_item("z", 200)
    # subtotal 200, coupon SAVE10 -> discount 20 => 180 + shipping 60 = 240
    assert cart.total(coupon="SAVE10") == 240.0

# With both member and coupon

def test_total_member_coupon(cart):
    cart.add_item("w", 800)
    # subtotal 800, coupon SAVE5 -> discount 40 => 760 + shipping half 30 = 790
    assert cart.total(member=True, coupon="SAVE05") == 790.0

# Coupon case-insensitivity and whitespace

def test_total_coupon_whitespace_case(cart):
    cart.add_item("v", 100)
    assert cart.total(coupon="   SaVe10  ") == pytest.approx(160.0, rel=1e-9)  # 90 +60 shipping

# Empty cart total is zero

def test_total_empty(cart):
    assert cart.total() == 0.0

# Invalid coupon raises ValueError in total

def test_total_invalid_coupon(cart):
    cart.add_item("u", 100)
    with pytest.raises(ValueError):
        cart.total(coupon="INVALID")

# Negative price or quantity should raise errors on add/remove

def test_add_negative_price_or_quantity(cart):
    with pytest.raises(ValueError):
        cart.add_item("bad", -10, 1)
    with pytest.raises(ValueError):
        cart.add_item("bad2", 10, 0)

# Removing negative quantity should raise ValueError

def test_remove_negative(cart):
    cart.add_item("good", 50, quantity=5)
    with pytest.raises(ValueError):
        cart.remove_item("good", -1)
