import pytest
import cart

# ------------------ function tests ---------------------------------

@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 105, 200])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ------------------ bulk discount ---------------------------------

@pytest.mark.parametrize("quantity,expected", [
    (1, 0),
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 2.5])
def test_bulk_discount_invalid_quantity_raises(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ------------------ coupon parsing ---------------------------------

@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    ("  SaVe5 ", 5),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVEX", "SAVEE100", "12345", "SAVE0", "SAVE51", ""])
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ------------------ shipping fee -----------------------------------

@pytest.mark.parametrize("subtotal,member,expected", [
    (999.99, False, 60),
    (1000, False, 0),
    (1200, True, 0),
    (50, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ------------------ Cart class -------------------------------------

@pytest.fixture
def empty_cart():
    return cart.Cart()

def test_add_item_new(empty_cart):
    empty_cart.add_item("apple", 1.0, 2)
    assert empty_cart.items() == {"apple": 2}

def test_add_item_existing_same_price(empty_cart):
    empty_cart.add_item("banana", 0.5, 3)
    empty_cart.add_item("banana", 0.5, 2)
    assert empty_cart.items() == {"banana": 5}

@pytest.mark.parametrize("unit_price", [-1, -0.01])
def test_add_item_negative_price_raises(empty_cart, unit_price):
    with pytest.raises(ValueError):
        empty_cart.add_item("orange", unit_price, 1)

@pytest.mark.parametrize("quantity", [0, -2, 1.5])
def test_add_item_invalid_quantity_raises(empty_cart, quantity):
    with pytest.raises(ValueError):
        empty_cart.add_item("pear", 0.7, quantity)

def test_add_item_price_mismatch(empty_cart):
    empty_cart.add_item("grape", 2.0, 1)
    with pytest.raises(ValueError):
        empty_cart.add_item("grape", 3.0, 1)

def test_remove_item_full_quantity(empty_cart):
    empty_cart.add_item("mango", 5.0, 4)
    empty_cart.remove_item("mango", 4)
    assert empty_cart.items() == {}

def test_remove_item_partial(empty_cart):
    empty_cart.add_item("melon", 2.5, 3)
    empty_cart.remove_item("melon", 1)
    assert empty_cart.items() == {"melon": 2}

@pytest.mark.parametrize("name", ["nonexistent"])
def test_remove_nonexistent_raises(empty_cart, name):
    with pytest.raises(KeyError):
        empty_cart.remove_item(name, 1)

# subtotal tests

def test_subtotal_basic():
    c = cart.Cart()
    c.add_item("pen", 2.0, 5)  # 10 -> no discount
    assert c.subtotal() == 10.0

def test_subtotal_bulk_discount():
    c = cart.Cart()
    c.add_item("book", 3.0, 12)  # quantity 12 => 5% discount
    expected = round(3.0 * 12 * (1 - 0.05), 2)
    assert c.subtotal() == expected

def test_subtotal_empty_cart():
    c = cart.Cart()
    assert c.subtotal() == 0

# total tests

def test_total_no_coupon_no_member():
    c = cart.Cart()
    c.add_item("tshirt", 20.0, 2)  # no bulk discount, subtotal=40
    expected = round(40 + 60, 2)  # shipping 60
    assert c.total() == expected

def test_total_with_coupon_and_member():
    c = cart.Cart()
    c.add_item("hat", 50.0, 1)
    # subtotal=50, coupon SAVE10 -> 45, member => shipping 30
    expected = round(45 + 30, 2)
    assert c.total(member=True, coupon="SAVE10") == expected

def test_total_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item("scarf", 15.0, 1)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")

# total empty cart

def test_total_empty_cart_zero_shipping():
    c = cart.Cart()
    assert c.total() == 0
