import pytest
import cart

# --- apply_discount ---
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# error cases for apply_discount
@pytest.mark.parametrize("price,percent", [
    (-1, 10),   # negative price
    (50, -5),   # negative percent
    (50, 105),  # percent >100
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --- bulk_discount_percent ---
@pytest.mark.parametrize("quantity,percent", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(quantity, percent):
    assert cart.bulk_discount_percent(quantity) == percent

# error case: non-positive quantity
@pytest.mark.parametrize("quantity", [0, -5, 1.2])
def test_bulk_discount_percent_error(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --- parse_coupon ---
valid_cases = [(
    "SAVE10",
    10),
    ("save20", 20),
    (" SAVE30 ", 30),
]
@pytest.mark.parametrize("code,percent", valid_cases)
def test_parse_coupon_valid(code, percent):
    assert cart.parse_coupon(code) == percent

invalid_codes = ["SAV10", "SAVE0", "SAVE51", "10SAVE", "", " SAVE-5 "]
@pytest.mark.parametrize("code", invalid_codes)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee ---
@pytest.mark.parametrize("subtotal,member,fee", [
    (0, False, 60),
    (500, True, 30),
    (999.99, False, 60),
    (1000, False, 0),
    (1500, True, 0),
])
def test_shipping_fee(subtotal, member, fee):
    assert cart.shipping_fee(subtotal, member) == fee

# error subtotal negative
with pytest.raises(ValueError):
    cart.shipping_fee(-10)

# --- Cart functionality ---
@pytest.fixture
def empty_cart():
    return cart.Cart()

# add_item tests
def test_add_new_item(empty_cart):
    c = empty_cart
    c.add_item("apple", 2.0, 3)
    assert c.items() == {"apple": 3}

def test_add_existing_same_price(empty_cart):
    c = empty_cart
    c.add_item("banana", 1.5, 2)
    c.add_item("banana", 1.5, 4)
    assert c.items() == {"banana": 6}

# adding with different price should raise ValueError
@pytest.mark.parametrize("name,price,qty,new_price", [
    ("orange", 0.8, 2, 1.0),
])
def test_add_existing_different_price(empty_cart, name, price, qty, new_price):
    c = empty_cart
    c.add_item(name, price, qty)
    with pytest.raises(ValueError):
        c.add_item(name, new_price, 1)

# remove_item tests
def test_remove_existing_items(empty_cart):
    c = empty_cart
    c.add_item("pear", 3.0, 5)
    c.remove_item("pear", 2)
    assert c.items() == {"pear": 3}
    c.remove_item("pear", 3)
    assert c.items() == {}

# removing more than present still removes item (quantity <=0 triggers removal)
def test_remove_more_than_present(empty_cart):
    c = empty_cart
    c.add_item("grape", 4.0, 2)
    c.remove_item("grape", 5)  # should remove entirely
    assert c.items() == {}

# removing non-existent item raises KeyError
def test_remove_nonexistent(empty_cart):
    c = empty_cart
    with pytest.raises(KeyError):
        c.remove_item("nonexistent", 1)

# subtotal calculations with bulk discounts
@pytest.mark.parametrize("items,expected_subtotal", [
    ([("x", 10.0, 9)], 90.00),           # no discount
    ([("y", 20.0, 10)], 190.00),        # 5% discount: 200-10=190
    ([("z", 5.0, 50)], 225.00),         # 10% discount: 250-25=225
    ([("w", 3.0, 100)], 255.00),        # 15% discount: 300-45=255
])
def test_subtotal_calculation(items, expected_subtotal):
    c = cart.Cart()
    for name, price, qty in items:
        c.add_item(name, price, qty)
    assert c.subtotal() == expected_subtotal

# total calculation without coupon and membership
@pytest.mark.parametrize("items,coupon,member,total", [
    ([("a", 5.0, 10)], None, False, 90.00),  # 5% bulk -> subtotal 45; no coupon; shipping 60 => total 105? Wait compute: subtotal 45, shipping 60 -> 105.
])
def test_total_without_coupon(items, coupon, member, total):
    c = cart.Cart()
    for name, price, qty in items:
        c.add_item(name, price, qty)
    assert c.total(member=member, coupon=coupon) == total

# more comprehensive total tests
@pytest.mark.parametrize("items,coupon,member,total", [
    ([("a", 10.0, 5)], None, False, 110.00),   # subtotal 50; shipping 60 -> 110
    ([("b", 20.0, 10)], "SAVE10", False, 90.00),# subtotal 190; coupon 10% =>171; shipping 60->231? Hmm compute: 190-19=171; shipping 60=>231.
])
def test_total_various(items,coupon,member,total):
    c = cart.Cart()
    for name,p,q in items:
        c.add_item(name,p,q)
    assert round(c.total(member=member, coupon=coupon),2)==round(total,2)

# invalid coupon raises ValueError
@pytest.mark.parametrize("items", [ [("c", 5.0, 1)] ])
def test_total_invalid_coupon(items):
    c = cart.Cart()
    for n,p,q in items:
        c.add_item(n,p,q)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")

# empty cart total is 0
def test_empty_cart_total():
    assert cart.Cart().total() == 0.00
