import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Tests for utility functions ----------

@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200.0, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
        (33.3333, 5, round(33.3333 * 0.95, 2)),
    ],
)
def test_apply_discount(price, percent, expected):
    assert apply_discount(price, percent) == pytest.approx(expected, rel=1e-9)

@pytest.mark.parametrize(
    "price,percent",
    [(-10, 5), (100, -1), (100, 101)],
)
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# bulk discount percentages
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (5, 0),
        (10, 5),
        (20, 5),
        (50, 10),
        (75, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# parse_coupon
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        ("  SaVe5 ", 5),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    ["SAVE0", "SAVE51", "DISCOUNT10", "SAVEX", " SAVE-10 ", ""]
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# shipping_fee
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (999.99, False, 60),
        (1000, False, 0),
        (1500, True, 30),
        (500, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Tests for Cart class ----------

def test_cart_initialization():
    cart = Cart()
    assert isinstance(cart.items(), dict) and len(cart.items()) == 0
    assert cart.subtotal() == 0
    assert cart.total() == pytest.approx(60.0)

# Adding items

def test_add_and_subtotal():
    cart = Cart()
    cart.add_item("apple", 10, quantity=3)   # subtotal 30
    cart.add_item("banana", 5)               # default quantity 1, subtotal 35
    assert cart.items()["apple"] == (10, 3)
    assert cart.items()["banana"] == (5, 1)
    assert cart.subtotal() == 35

# Removing items

def test_remove_item():
    cart = Cart()
    cart.add_item("orange", 8, quantity=5)   # subtotal 40
    cart.remove_item("orange", quantity=2)   # remaining quantity 3
    assert cart.items()["orange"] == (8, 3)
    assert cart.subtotal() == 24
    # Removing more than exists should raise ValueError
    with pytest.raises(ValueError):
        cart.remove_item("orange", quantity=5)

# Bulk discount application in total

def test_bulk_discount_in_total():
    cart = Cart()
    cart.add_item("widget", 20, quantity=60)   # bulk 10% discount per item
    # subtotal before discount: 1200
    expected_subtotal_after_disc = round(1200 * 0.90, 2)
    assert cart.subtotal() == 1200
    total_without_shipping = expected_subtotal_after_disc + shipping_fee(1200)
    assert cart.total(coupon=None) == pytest.approx(total_without_shipping)

# Coupon discount

def test_coupon_discount():
    cart = Cart()
    cart.add_item("gadget", 50, quantity=2)   # subtotal 100
    total_before = cart.total()  # includes shipping (60)
    assert total_before == pytest.approx(160.0)
    # apply coupon SAVE10 -> 10% discount on entire order
    total_after_coupon = cart.total(coupon="SAVE10")
    expected_discounted = round((100 + 60) * 0.90, 2)
    assert total_after_coupon == pytest.approx(expected_discounted)

# Member discount on shipping only (via shipping_fee logic already tested in Cart via total)

def test_member_shipping():
    cart = Cart()
    cart.add_item("book", 200, quantity=5)   # subtotal 1000 -> free shipping
    assert cart.total(member=True) == pytest.approx(1000.0)
    # change to lower subtotal to trigger shipping fee
    cart.remove_item("book")  # remove one, quantity now 4, subtotal 800
    total_nonmember = cart.total()
    total_member = cart.total(member=True)
    assert total_nonmember == pytest.approx(800 + 60)
    assert total_member == pytest.approx(800 + 30)

# Ensure coupon parsing is case-insensitive and whitespace stripped in Cart.total

def test_coupon_whitespace_and_case():
    cart = Cart()
    cart.add_item("pen", 5, quantity=10)   # subtotal 50
    total1 = cart.total(coupon="  SaVe20 ")
    expected1 = round((50 + shipping_fee(50)) * 0.80, 2)
    assert total1 == pytest.approx(expected1)

# Error conditions for Cart methods

def test_cart_errors():
    cart = Cart()
    with pytest.raises(ValueError):
        cart.add_item("bad", -5)
    with pytest.raises(ValueError):
        cart.add_item("zero", 10, quantity=0)
    with pytest.raises(KeyError):
        cart.remove_item("nonexistent")
