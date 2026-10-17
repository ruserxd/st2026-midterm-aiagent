import pytest
import cart

# Helper to create a simple cart with one item

def make_cart(**kwargs):
    c = cart.Cart()
    for name, (price, qty) in kwargs.items():
        c.add_item(name, price, qty)
    return c

# --- apply_discount tests ---
@pytest.mark.parametrize("price, percent, expected", [
    (200.0, 15, 170.0),
    (100.0, 0, 100.0),
    (50.5, 20, 40.4),
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# boundary and error cases for apply_discount
@pytest.mark.parametrize("price, percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --- bulk_discount_percent tests ---
@pytest.mark.parametrize("quantity, expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (250, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# error case for bulk_discount_percent
@pytest.mark.parametrize("quantity", [0, -5, 2.3])
def test_bulk_discount_percent_error(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --- parse_coupon tests ---
@pytest.mark.parametrize("code, expected", [
    ("SAVE10", 10),
    ("save20 ", 20),
    ("  SaVe5", 5),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# error cases for parse_coupon
@pytest.mark.parametrize("code", ["SAVE0", "SAVEX", "10SAVE", "sve10", "SAVE51"]) 
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee tests ---
@pytest.mark.parametrize("subtotal, member, expected", [
    (0, False, 60),
    (500, True, 30),
    (999.99, False, 60),
    (1000, False, 0),
    (1500, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# error case for shipping_fee
@pytest.mark.parametrize("subtotal", [-1, -100.5])
def test_shipping_fee_error(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --- Cart tests ---

# add_item and items

def test_add_and_items():
    c = cart.Cart()
    c.add_item("apple", 1.0, 3)
    c.add_item("banana", 0.5, 2)
    assert c.items() == {"apple": 3, "banana": 2}

# adding existing item increases quantity and requires same unit_price

def test_add_existing_same_price():
    c = cart.Cart()
    c.add_item("orange", 0.8, 1)
    c.add_item("orange", 0.8, 4)
    assert c.items() == {"orange": 5}

# adding existing item with different price raises ValueError

def test_add_existing_different_price_error():
    c = cart.Cart()
    c.add_item("pear", 1.2, 1)
    with pytest.raises(ValueError):
        c.add_item("pear", 1.3, 1)

# remove_item behavior

def test_remove_item():
    c = cart.Cart()
    c.add_item("milk", 1.5, 4)
    c.remove_item("milk", 2)
    assert c.items() == {"milk": 2}
    c.remove_item("milk", 2)
    assert "milk" not in c.items()

# removing more than exists removes the item entirely

def test_remove_more_than_exists():
    c = cart.Cart()
    c.add_item("juice", 2.0, 3)
    c.remove_item("juice", 5)  # should remove completely
    assert c.items() == {}

# removing non-existent item raises KeyError

def test_remove_nonexistent_error():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("bread", 1)

# subtotal calculation with bulk discount and rounding

def test_subtotal_with_discount_and_rounding():
    c = cart.Cart()
    # 9 units -> no bulk discount, 10 units -> 5% discount
    c.add_item("pen", 2.0, 9)
    c.add_item("notebook", 5.0, 10)  # should get 5% off on notebook subtotal
    # pen: 2*9 = 18.00
    # notebook before discount: 5*10 = 50.00; bulk percent 5 -> 47.50
    expected_subtotal = round(18.0 + 47.5, 2)
    assert c.subtotal() == expected_subtotal

# subtotal of empty cart is 0

def test_empty_cart_subtotal():
    assert cart.Cart().subtotal() == 0

# total with coupon and shipping fee

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("shoes", 200.0, 1)   # subtotal 200
    subtotal_after_discount = 200.0
    # apply coupon SAVE10 -> 20% off (parse_coupon returns 10)
    after_coupon = cart.apply_discount(subtotal_after_discount, cart.parse_coupon("SAVE10"))
    # shipping on amount after coupon: after_coupon < 1000 -> fee 60
    expected_total = round(after_coupon + cart.shipping_fee(after_coupon), 2)
    assert c.total(coupon="SAVE10") == expected_total

# total with member discount via shipping (member flag) and no coupon

def test_total_member_shipping():
    c = cart.Cart()
    c.add_item("watch", 300.0, 1)  # subtotal 300
    # no coupon -> amount stays 300
    # shipping for member: 30
    expected_total = round(300 + 30, 2)
    assert c.total(member=True) == expected_total

# total on empty cart is 0 (no shipping)

def test_empty_cart_total():
    assert cart.Cart().total() == 0

# invalid coupon in total raises ValueError

def test_total_invalid_coupon_error():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# subtotal and total should be independent of member flag unless shipping applies

def test_member_flag_affects_only_shipping():
    c = cart.Cart()
    c.add_item("book", 150.0, 1)
    # subtotal same regardless
    assert c.subtotal() == 150.0
    # total without shipping: no coupon -> 150 + 60 (shipping) = 210
    assert c.total() == 210.0
    # member gets half shipping: 150 + 30 = 180
    assert c.total(member=True) == 180.0
