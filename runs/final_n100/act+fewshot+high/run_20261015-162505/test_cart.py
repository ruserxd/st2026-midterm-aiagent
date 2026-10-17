import pytest
import cart

# Helper functions based on specification
def expected_apply_discount(price, percent):
    if price < 0:
        raise ValueError("price must be non-negative")
    if not (0 <= percent <= 100):
        raise ValueError("percent must be between 0 and 100")
    return round(price * (100 - percent) / 100, 2)

def expected_shipping_fee(subtotal, member=False):
    if subtotal < 0:
        raise ValueError("subtotal must be non-negative")
    threshold = cart.FREE_SHIPPING_THRESHOLD
    base = cart.SHIPPING_BASE
    if subtotal >= threshold:
        return 0
    fee = base
    if member:
        fee /= 2
    return fee

def expected_total(cart_obj, member=False, coupon=None):
    amount = cart_obj.subtotal()
    if coupon is not None:
        percent = cart.parse_coupon(coupon)
        amount = expected_apply_discount(amount, percent)
    shipping = expected_shipping_fee(amount, member)
    return round(amount + shipping, 2)

# -------------------- Tests for functions --------------------
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),
        (10, 33, 6.7),     # round(6.7,2) == 6.7
        (0, 100, 0.0),
        (50, 0, 50.0),
    ]
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price,percent",
    [
        (-1, 10),   # negative price
        (10, -5),   # negative percent
        (10, 110),  # percent >100
    ]
)
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

@pytest.mark.parametrize(
    "quantity,expected",
    [
        (5, 0),
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),   # spec expects 10
        (51, 10),
        (99, 10),
        (100, 15),
        (150, 15),
    ]
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -5, 3.5, 'a'],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),      # spec requires case-insensitive
        ("   SAVE30   ", 30),
        ("SaVe40", 40),     # mixed case
        ("SAVE1", 1),
        ("SAVE50", 50),
    ]
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "SAVE0",          # percent below 1
        "SAVE51",         # percent above 50
        "SAVExx",         # non-digit suffix
        "SAV30",          # wrong prefix
        "",               # empty string
        "SAVE",           # no digits
        None,             # not a string
    ]
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Verify constants exist for shipping fee tests
def test_cart_constants_exist():
    assert hasattr(cart, "FREE_SHIPPING_THRESHOLD")
    assert hasattr(cart, "SHIPPING_BASE")

threshold = cart.FREE_SHIPPING_THRESHOLD
base = cart.SHIPPING_BASE

@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (max(0.01, threshold - 1), False, base),
        (max(0.01, threshold - 1), True, base / 2),
        (threshold + 10, False, 0),
    ]
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-5, -100])
def test_shipping_fee_negative_subtotal(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# -------------------- Tests for Cart class --------------------
def test_cart_init_empty():
    c = cart.Cart()
    assert isinstance(c, cart.Cart)
    assert c.items() == {}

def test_cart_add_item_new():
    c = cart.Cart()
    c.add_item("apple", 1.5, 2)
    assert c.items() == {"apple": 2}

def test_cart_add_existing_same_price():
    c = cart.Cart()
    c.add_item("apple", 1.5, 2)
    c.add_item("apple", 1.5, 3)
    assert c.items() == {"apple": 5}

def test_cart_add_existing_price_mismatch():
    c = cart.Cart()
    c.add_item("apple", 1.5, 2)
    with pytest.raises(ValueError):
        c.add_item("apple", 2.0, 1)

@pytest.mark.parametrize(
    "unit_price,quantity",
    [
        (-1, 1),      # negative unit price
        (1, 0),       # zero quantity
        (1, -3),      # negative quantity
        (1, 2.5),     # non-integer quantity
    ]
)
def test_cart_add_item_invalid(unit_price, quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("banana", unit_price, quantity)

def test_cart_remove_partial():
    c = cart.Cart()
    c.add_item("apple", 1.0, 5)
    c.remove_item("apple", 2)
    assert c.items() == {"apple": 3}

def test_cart_remove_zero_and_less_than_current():
    c = cart.Cart()
    c.add_item("apple", 1.0, 5)
    c.remove_item("apple", 10)   # should delete the item
    assert "apple" not in c.items()

def test_cart_remove_to_zero():
    c = cart.Cart()
    c.add_item("orange", 2.0, 3)
    c.remove_item("orange", 3)   # quantity reaches zero
    assert "orange" not in c.items()

def test_cart_remove_nonexistent_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent")

def test_cart_items_multiple():
    c = cart.Cart()
    c.add_item("apple", 1.0, 2)
    c.add_item("banana", 3.5, 4)
    assert c.items() == {"apple": 2, "banana": 4}

def test_cart_subtotal_basic():
    c = cart.Cart()
    c.add_item("a", 10.0, 3)   # 30
    c.add_item("b", 5.0, 2)    # 10 => total 40
    assert c.subtotal() == round(40.0, 2)

def test_cart_subtotal_with_discounts():
    c = cart.Cart()
    c.add_item("a", 2, 9)      # qty=9 -> no discount, line_total=18
    c.add_item("b", 10, 10)    # qty=10 -> 5% discount, line_total=95
    c.add_item("c", 3, 50)     # qty=50 -> 10% discount per spec, line_total=135
    assert c.subtotal() == round(18 + 95 + 135, 2)

def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0

def test_cart_total_no_coupon_non_member():
    c = cart.Cart()
    c.add_item("apple", 10.0, 5)   # subtotal=50
    assert c.total() == expected_total(c)

def test_cart_total_with_coupon_non_member():
    c = cart.Cart()
    c.add_item("apple", 10.0, 5)
    coupon_code = "SAVE10"
    assert c.total(member=False, coupon=coupon_code) == expected_total(c, member=False, coupon=coupon_code)

def test_cart_total_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item("apple", 10.0, 5)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")

def test_cart_total_shipping_after_coupon_threshold():
    # Build a cart where original subtotal is above free threshold but
    # applying the coupon brings it below that threshold.
    price = cart.FREE_SHIPPING_THRESHOLD + 1
    c = cart.Cart()
    c.add_item("expensive", price, 1)
    coupon_code = "SAVE50"
    assert c.total(member=False, coupon=coupon_code) == expected_total(c, member=False, coupon=coupon_code)

def test_cart_total_shipping_after_coupon_threshold_member():
    price = cart.FREE_SHIPPING_THRESHOLD + 1
    c = cart.Cart()
    c.add_item("expensive", price, 1)
    coupon_code = "SAVE50"
    assert c.total(member=True, coupon=coupon_code) == expected_total(c, member=True, coupon=coupon_code)
