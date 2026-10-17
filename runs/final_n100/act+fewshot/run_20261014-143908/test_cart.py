import pytest
import cart

# ---------- utility helpers for expected calculations ----------

def apply_discount(price, percent):
    if price < 0:
        raise ValueError
    if not 0 <= percent <= 100:
        raise ValueError
    return round(price * (1 - percent / 100), 2)

# test helper to compute bulk discount percent via spec

def bulk_discount_percent(quantity):
    if quantity < 1 or int(quantity) != quantity:
        raise ValueError
    q = int(quantity)
    if q >= 100:
        return 15
    if q >= 50:
        return 10
    if q >= 10:
        return 5
    return 0

# ---------- tests for standalone functions ----------

@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (123.456, 10, 111.11),  # round to 2 decimals
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid_args(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk discount tests
@pytest.mark.parametrize("quantity,expected", [
    (9, 0), (10, 5), (49, 5), (50, 10), (99, 10), (100, 15), (150, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 5.5, "a"])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize("code,percent", [
    ("SAVE10", 10),
    ("save20", 20),
    ("  SaVe50  ", 50),
])
def test_parse_coupon_valid(code, percent):
    assert cart.parse_coupon(code) == percent

@pytest.mark.parametrize("code", ["SAVEX", "DISCOUNT", "SAVE0", "SAVE51", "save-10", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal,member,expected", [
    (1200, False, 0), (1200, True, 0),
    (999.99, False, 60), (999.99, True, 30),
    (0, False, 60), (0, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class tests ----------

@pytest.fixture
def empty_cart():
    return cart.Cart()

def test_initial_state(empty_cart):
    assert empty_cart.items() == {}
    assert empty_cart.subtotal() == 0.0
    assert empty_cart.total() == 0.0

# adding items

def test_add_item_basic(empty_cart):
    empty_cart.add_item("apple", 1.00, 3)
    assert empty_cart.items() == {"apple": 3}
    assert empty_cart.subtotal() == 3.0

# adding same item with same price increases quantity

def test_add_item_increment(empty_cart):
    empty_cart.add_item("banana", 2.5, 1)
    empty_cart.add_item("banana", 2.5, 4)
    assert empty_cart.items() == {"banana": 5}
    assert empty_cart.subtotal() == 12.5

# adding same item with different price raises error

def test_add_item_price_mismatch(empty_cart):
    empty_cart.add_item("cherry", 0.5, 2)
    with pytest.raises(ValueError):
        empty_cart.add_item("cherry", 0.6, 1)

# remove item tests

def test_remove_item_basic(empty_cart):
    empty_cart.add_item("date", 3.0, 4)
    empty_cart.remove_item("date", 2)
    assert empty_cart.items() == {"date": 2}

# removing more than existing removes it completely

def test_remove_item_overflow(empty_cart):
    empty_cart.add_item("egg", 1.0, 3)
    empty_cart.remove_item("egg", 5)
    assert empty_cart.items() == {}

# removing non-existent item raises KeyError

def test_remove_nonexistent(empty_cart):
    with pytest.raises(KeyError):
        empty_cart.remove_item("fig", 1)

# subtotal calculation with bulk discount

def test_subtotal_with_bulk_discount(empty_cart):
    empty_cart.add_item("grape", 2.0, 12)  # qty>=10 =>5% discount
    expected = round(2.0 * 12 * (1 - 5/100), 2)
    assert empty_cart.subtotal() == expected

# total without coupon and member

def test_total_without_coupon_and_member(empty_cart):
    empty_cart.add_item("honey", 10.0, 1)  # subtotal 10
    expected = round(10 + 60, 2)
    assert empty_cart.total() == expected

# total with member shipping

def test_total_member_shipping(empty_cart):
    empty_cart.add_item("icecream", 5.0, 1)
    expected = round(5 + 30, 2)
    assert empty_cart.total(member=True) == expected

# total with coupon discount

def test_total_with_coupon(empty_cart):
    empty_cart.add_item("jam", 100.0, 1)
    # apply SAVE10 => 90, shipping fee still 60
    expected = round(90 + 60, 2)
    assert empty_cart.total(coupon="SAVE10") == expected

# total with invalid coupon raises ValueError

def test_total_invalid_coupon(empty_cart):
    empty_cart.add_item("kettle", 50.0, 1)
    with pytest.raises(ValueError):
        empty_cart.total(coupon="INVALID")

# total on empty cart costs zero no shipping

def test_total_empty_cart(empty_cart):
    assert empty_cart.total() == 0.0
