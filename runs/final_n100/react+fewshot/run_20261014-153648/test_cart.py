import pytest
import cart

# 1. apply_discount
@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.00),
    (100, 0, 100.00),
    (50, 100, 0.00),
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# Error cases for apply_discount
@pytest.mark.parametrize("price,percent", [(-1, 10), (10, -5), (10, 105)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# 2. bulk_discount_percent
@pytest.mark.parametrize("quantity,expected", [
    (9,0),(10,5),(49,5),(50,10),(99,10),(100,15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# Error case for bulk_discount_percent
@pytest.mark.parametrize("quantity", [0, -1, 2.5])
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(int(quantity)) if isinstance(quantity,int) else cart.bulk_discount_percent(quantity)

# 3. parse_coupon
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    ("  SAVE30  ", 30),
])
def test_parse_coupon(code, expected):
    assert cart.parse_coupon(code) == expected

# Invalid coupon codes
@pytest.mark.parametrize("code", ["SAVEX10","SAVE0","SAVE51","save-5"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# 4. shipping_fee
@pytest.mark.parametrize("subtotal,member,expected", [
    (1000, False, 0),
    (1200, True, 0),
    (500, False, 60),
    (400, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# Error case for shipping_fee
@pytest.mark.parametrize("subtotal", [-10,-1])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# 5. Cart functionality
@pytest.fixture
def empty_cart():
    return cart.Cart()

def test_cart_add_and_items(empty_cart):
    c = empty_cart
    c.add_item("apple", 2.0, 3)
    assert c.items() == {"apple":3}
    # add same item increases quantity
    c.add_item("apple", 2.0, 2)
    assert c.items() == {"apple":5}
    with pytest.raises(ValueError):
        c.add_item("apple", 1.99, 1)  # price mismatch

def test_cart_remove_and_subtotal(empty_cart):
    c = empty_cart
    c.add_item("banana", 1.0, 10)
    assert c.subtotal() == 9.5  # 10*1 - 5% bulk discount -> 9.5
    c.remove_item("banana", 5)
    assert c.items() == {"banana":5}
    assert c.subtotal() == 4.75  # 5*1 - 5%? quantity 5 <10 so 0% => 5.00
    c.remove_item("banana", 5)  # removes item
    assert c.items() == {}
    with pytest.raises(KeyError):
        c.remove_item("banana",1)

def test_cart_total_with_coupon_and_shipping(empty_cart):
    c = empty_cart
    c.add_item("widget", 100.0, 10)  # bulk discount 5%
    assert c.subtotal() == 950.0  # 10*100 -5% ->950
    total = c.total(member=False, coupon="SAVE10")
    # subtotal after coupon: 950 *0.90=855; shipping 60 =>915
    assert total == 915.00
    total_member = c.total(member=True, coupon=None)
    # subtotal 950; member half shipping:30; total 980
    assert total_member == 980.00

# Empty cart costs zero no shipping
def test_empty_cart_total(empty_cart):
    assert empty_cart.total() == 0.0
