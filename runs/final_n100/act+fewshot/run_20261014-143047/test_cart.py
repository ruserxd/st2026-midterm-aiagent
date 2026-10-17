import pytest
import cart

# ---- basic helpers -------------------------------------------------------

def round_2(x):
    return round(float(x), 2)

# ---- function tests -----------------------------------------------------

@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),   # example from spec
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# boundary tests for price and percent
@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [101, 150, -1])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# bulk discount percent
@pytest.mark.parametrize("qty,expected", [
    (5, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -1, 3.5])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(int(qty)) if isinstance(qty, int) else cart.bulk_discount_percent(qty)

# parse_coupon
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save5", 5),
    (" SAVE25 ", 25),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAV10",          # wrong prefix
    "SAVE0",          # below 1
    "SAVE51",         # above 50
    "12345",          # not a code
    "SAVE-5",         # negative
    "save101",        # >50
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping fee
@pytest.mark.parametrize("subtotal,member,result", [
    (1000, False, 0),
    (1001, True, 0),   # free if subtotal >= 1000 regardless of member
    (999.99, False, 60),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, result):
    assert cart.shipping_fee(subtotal, member) == result

@pytest.mark.parametrize("subtotal", [-1, -0.01])
def test_shipping_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Cart class tests ----------------------------------------------------

@pytest.fixture
def empty_cart():
    return cart.Cart()

# items() returns dict of name->quantity

def test_items_initial(empty_cart):
    assert empty_cart.items() == {}

# add_item adds and increments correctly, raises on mismatched price or bad args

def test_add_and_increment(empty_cart):
    c = empty_cart
    c.add_item("apple", 1.0)
    assert c.items() == {"apple": 1}
    c.add_item("apple", 1.0, quantity=2)
    assert c.items() == {"apple": 3}
    # adding with different price should raise
    with pytest.raises(ValueError):
        c.add_item("apple", 1.5)

# test add_item validation
@pytest.mark.parametrize("unit_price,quantity", [
    (-1, 1), (0.5, -2), (10, 0),
])
def test_add_invalid(empty_cart, unit_price, quantity):
    with pytest.raises(ValueError):
        empty_cart.add_item("test", unit_price, quantity)

# remove_item: removal and deletion when qty <= 0

def test_remove_and_deletion(empty_cart):
    c = empty_cart
    c.add_item("banana", 2.0, quantity=3)
    c.remove_item("banana")
    assert c.items() == {"banana": 2}
    c.remove_item("banana", quantity=2)
    assert c.items() == {}

# removing non-existent raises KeyError

def test_remove_nonexistent(empty_cart):
    with pytest.raises(KeyError):
        empty_cart.remove_item("pear")

# subtotal calculation with bulk discounts

def test_subtotal_with_bulk_discount():
    c = cart.Cart()
    # 10 apples at $1 each: bulk discount 5% -> 0.95 per apple
    c.add_item("apple", 1.0, quantity=10)
    expected = round_2(10 * 1.0 * (1 - 0.05))
    assert round_2(c.subtotal()) == expected
    # adding 5 oranges at $2 each: no bulk discount
    c.add_item("orange", 2.0, quantity=5)
    total = round_2(10 * 1.0 * (1 - 0.05) + 5 * 2.0)
    assert round_2(c.subtotal()) == total

# subtotal of empty cart is 0

def test_empty_subtotal(empty_cart):
    assert empty_cart.subtotal() == 0

# total calculation: coupon, shipping, rounding

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    # 100 items at $10 each -> bulk discount 15% for that item
    c.add_item("widget", 10.0, quantity=100)
    subtotal_before = round_2(100 * 10.0 * (1 - 0.15))
    assert round_2(c.subtotal()) == subtotal_before
    # apply coupon SAVE20 => reduce by 20%
    total_after_coupon = round_2(subtotal_before * (1 - 0.20))
    shipping = cart.shipping_fee(total_after_coupon, member=False)
    expected_total = round_2(total_after_coupon + shipping)
    assert round_2(c.total(coupon="SAVE20")) == expected_total

# total with member discount on shipping

def test_member_shipping_discount():
    c = cart.Cart()
    c.add_item("gadget", 5.0, quantity=10)  # subtotal 45 after 5% bulk
    subtotal_before = round_2(10 * 5.0 * (1 - 0.05))
    assert round_2(c.subtotal()) == subtotal_before
    total_after_coupon = subtotal_before  # no coupon
    shipping_member = cart.shipping_fee(total_after_coupon, member=True)
    expected_total = round_2(total_after_coupon + shipping_member)
    assert round_2(c.total(member=True)) == expected_total

# total on empty cart is 0, no shipping

def test_total_empty_cart(empty_cart):
    assert empty_cart.total() == 0

# invalid coupon raises ValueError in total

def test_invalid_coupon_in_total(empty_cart):
    with pytest.raises(ValueError):
        empty_cart.total(coupon="BADCODE")
