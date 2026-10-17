import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# --- Tests for standalone functions -------------------------------------------------

def test_apply_discount_valid():
    assert apply_discount(200, 15) == 170.0
    # rounding check
    assert apply_discount(99.99, 33) == round(99.99 * 0.67, 2)

# boundary conditions for percent and price
@pytest.mark.parametrize(
    "price,percent",
    [(-1, 10), (10, -5), (10, 105)],
)
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# bulk discount logic
@pytest.mark.parametrize(
    "qty,expected",
    [(1, 0), (9, 0), (10, 5), (49, 5), (50, 10), (99, 10), (100, 15), (200, 15)],
)
def test_bulk_discount_percent(qty, expected):
    assert bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -1])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)

# coupon parsing
@pytest.mark.parametrize(
    "code,expected",
    [("SAVE10", 10), ("save20", 20), (" SAVE30 ", 30)],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVEXX", "SAVED", "foo", "SAVE51", "", "  "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# shipping fee rules
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [(0, False, 60), (500, True, 30), (999.99, False, 60), (1000, False, 0), (1500, True, 0)],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# --- Tests for Cart class -----------------------------------------------------------

@pytest.fixture
def cart_obj():
    return Cart()

# adding items and checking internal representation via items() method

def test_add_item(cart_obj):
    cart_obj.add_item("apple", 100, 3)
    assert cart_obj.items() == {"apple": (100, 3)}
    # add another product
    cart_obj.add_item("banana", 50)
    assert cart_obj.items()["banana"] == (50, 1)

# removing items decreases quantity or removes key when zero

def test_remove_item(cart_obj):
    cart_obj.add_item("apple", 100, 3)
    cart_obj.remove_item("apple", 2)
    assert cart_obj.items()["apple"] == (100, 1)
    cart_obj.remove_item("apple")  # default quantity=1
    assert "apple" not in cart_obj.items()

# subtotal calculation with bulk discount applied per item type

def test_subtotal(cart_obj):
    cart_obj.add_item("item", 10, 12)  # bulk discount 5%
    expected = apply_discount(10 * 12, 5)
    assert cart_obj.subtotal() == expected

# total includes shipping and member discounts (apply_coupon) if provided

def test_total_without_coupons(cart_obj):
    cart_obj.add_item("item", 10, 1)
    # subtotal 10 -> no bulk discount
    assert cart_obj.total(member=False, coupon=None) == apply_discount(10 + shipping_fee(10), 0)

# member gets half shipping fee

def test_total_member(cart_obj):
    cart_obj.add_item("item", 100, 1)
    expected = apply_discount(100 + shipping_fee(100, member=True), 0)
    assert cart_obj.total(member=True) == expected

# coupon applied after subtotal but before shipping

def test_total_coupon(cart_obj):
    cart_obj.add_item("item", 10, 1)
    discounted = apply_discount(10, 10)  # 10% coupon
    expected = apply_discount(discounted + shipping_fee(discounted), 0)
    assert cart_obj.total(coupon="SAVE10") == expected

# coupon with invalid code should raise ValueError

def test_total_coupon_invalid(cart_obj):
    cart_obj.add_item("item", 10, 1)
    with pytest.raises(ValueError):
        cart_obj.total(coupon="INVALID")
