import pytest
import cart

def round2(x):
    return round(float(x), 2)

# apply_discount tests remain same
@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == round2(expected)

@pytest.mark.parametrize("price,percent", [(-1,10),(10,-5),(10,150)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent tests corrected
@pytest.mark.parametrize("qty,expected", [
    (9,0),
    (10,5),
    (49,5),
    (50,10),
    (99,10),
    (100,15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0,-5])
def test_bulk_discount_percent_errors(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# parse_coupon tests: expect case-insensitive
@pytest.mark.parametrize("code,expected", [
    ("SAVE10",10),
    ("save25",25),
    (" SAVE50 ",50),
])
def test_parse_coupon(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0","SAVE51","foo10","SAVEXX","  " ])
def test_parse_coupon_errors(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal,member,expected", [
    (1000, False, 0),
    (1200, True, 0),
    (999.99, False, 60),
    (50, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1,-100])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart fixture
@pytest.fixture
def empty_cart():
    return cart.Cart()

# Adding items
def test_add_item_new(empty_cart):
    empty_cart.add_item("apple", 1.0, 3)
    assert empty_cart.items() == {"apple":3}

def test_add_item_increase_quantity(empty_cart):
    empty_cart.add_item("banana", 2.5, 2)
    empty_cart.add_item("banana", 2.5, 1)
    assert empty_cart.items() == {"banana":3}

def test_add_item_price_mismatch(empty_cart):
    empty_cart.add_item("orange", 0.8, 5)
    with pytest.raises(ValueError):
        empty_cart.add_item("orange", 1.0, 2)

# Remove items
def test_remove_item_partial_and_full(empty_cart):
    empty_cart.add_item("pear", 3.0, 4)
    empty_cart.remove_item("pear", 2)
    assert empty_cart.items() == {"pear":2}
    empty_cart.remove_item("pear", 2)
    assert empty_cart.items() == {}

def test_remove_nonexistent(empty_cart):
    with pytest.raises(KeyError):
        empty_cart.remove_item("mango",1)

# Subtotal calculation corrected
@pytest.mark.parametrize("items,expected_subtotal", [
    ([("a",10.0,5)], 50.0),   # 5 units -> no discount
    ([("b",20.0,50)], 900.0), # 50 units ->10% discount
])
def test_subtotal(items, expected_subtotal):
    c = cart.Cart()
    for name, price, qty in items:
        c.add_item(name, price, qty)
    assert c.subtotal() == round2(expected_subtotal)

# Total tests
def test_total_no_coupon_member(empty_cart):
    empty_cart.add_item("item", 10.0, 1)
    expected = round2(10 + cart.shipping_fee(10))
    assert empty_cart.total() == expected

def test_total_member_shipping(empty_cart):
    empty_cart.add_item("item", 50.0, 1)
    expected = round2(50 + cart.shipping_fee(50, True))
    assert empty_cart.total(member=True) == expected

def test_total_coupon(empty_cart):
    empty_cart.add_item("item", 100.0, 1)
    subtotal = 100.0
    after_coupon = cart.apply_discount(subtotal,10) # SAVE10 ->10%
    shipping = cart.shipping_fee(after_coupon)
    expected = round2(after_coupon + shipping)
    assert empty_cart.total(coupon="SAVE10") == expected

def test_total_invalid_coupon(empty_cart):
    empty_cart.add_item("item", 20.0,1)
    with pytest.raises(ValueError):
        empty_cart.total(coupon="BAD")

def test_empty_cart_total():
    c = cart.Cart()
    assert c.total() == 0.0
