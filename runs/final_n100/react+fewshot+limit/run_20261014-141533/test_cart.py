import pytest
import cart

# --- apply_discount ---------------------------------------------------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),            # example
    (100, 0, 100.0),             # no discount
    (50, 100, 0.0),              # full discount
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# boundary price negative should raise
@pytest.mark.parametrize("price,percent", [(-1, 10), (10, -5), (10, 105)])
def test_apply_discount_invalid_args(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --- bulk_discount_percent ---------------------------------------------
@pytest.mark.parametrize("quantity,percent", [
    (5, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, percent):
    assert cart.bulk_discount_percent(quantity) == percent

# invalid quantity
@pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --- parse_coupon -----------------------------------------------------
valid_codes = {
    "SAVE10": 10,
    "save50": 50,
    " SAVE25 ": 25,
}
@pytest.mark.parametrize("code,expected", valid_codes.items())
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# invalid codes
invalid = ["SAV10", "SAVE0", "SAVE51", "foo", "", "  "]
@pytest.mark.parametrize("code", invalid)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee -----------------------------------------------------
@pytest.mark.parametrize("subtotal,member,fee", [
    (0, False, 60),
    (500, True, 30),
    (999.99, False, 60),
    (1000, False, 0),
    (2000, True, 0),
])
def test_shipping_fee(subtotal, member, fee):
    assert cart.shipping_fee(subtotal, member) == fee

# negative subtotal raises
@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --- Cart class -------------------------------------------------------
@pytest.fixture
def empty_cart():
    return cart.Cart()

# add_item basic behavior

def test_add_item_new(empty_cart):
    empty_cart.add_item("apple", 1.0, 3)
    assert empty_cart.items() == {"apple": 3}

# adding same item increases quantity and requires same unit_price

def test_add_item_increment(empty_cart):
    empty_cart.add_item("banana", 2.5)
    empty_cart.add_item("banana", 2.5, 2)
    assert empty_cart.items() == {"banana": 3}

# mismatch price raises

def test_add_item_price_mismatch(empty_cart):
    empty_cart.add_item("orange", 1.0)
    with pytest.raises(ValueError):
        empty_cart.add_item("orange", 2.0)

# invalid args
@pytest.mark.parametrize("unit_price,quantity", [(-1, 1), (1.0, -5), (1.0, 0)])
def test_add_item_invalid_args(unit_price, quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("foo", unit_price, quantity)

# remove_item tests

def test_remove_item(empty_cart):
    empty_cart.add_item("pear", 3.0, 4)
    empty_cart.remove_item("pear", 2)
    assert empty_cart.items() == {"pear": 2}

# removing more than exists removes item

def test_remove_item_over(empty_cart):
    empty_cart.add_item("grape", 0.5, 1)
    empty_cart.remove_item("grape", 2)
    assert empty_cart.items() == {}

# remove non-existent raises KeyError

def test_remove_item_missing(empty_cart):
    with pytest.raises(KeyError):
        empty_cart.remove_item("doesnotexist")

# subtotal calculation with bulk discount

def test_subtotal_basic():
    c = cart.Cart()
    c.add_item("item", 10.0, 5)   # no discount
    assert c.subtotal() == 50.0

def test_subtotal_bulk_discount():
    c = cart.Cart()
    c.add_item("item", 20.0, 10)  # 5% bulk discount
    expected = round(20.0 * 10 * (1 - 0.05), 2)
    assert c.subtotal() == expected

# total with coupon and shipping

def test_total_no_coupon():
    c = cart.Cart()
    c.add_item("item", 100.0, 5)  # no bulk discount
    amount = 500.0  # subtotal
    fee = cart.shipping_fee(amount)
    assert c.total() == round(amount + fee, 2)

def test_total_with_coupon_and_member():
    c = cart.Cart()
    c.add_item("item", 200.0, 5)  # no bulk discount
    subtotal = 1000.0
    coupon_discount = subtotal * 0.10  # assume SAVE10
    after_coupon = subtotal - coupon_discount
    fee = cart.shipping_fee(after_coupon, member=True)
    total_expected = round(after_coupon + fee, 2)
    assert c.total(member=True, coupon="SAVE10") == total_expected

# empty cart total is 0

def test_total_empty_cart():
    assert cart.Cart().total() == 0
