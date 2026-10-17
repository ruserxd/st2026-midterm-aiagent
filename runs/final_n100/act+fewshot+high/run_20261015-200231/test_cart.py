import pytest
import cart

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(0, 50) == 0.0
    # Rounding cases
    assert cart.apply_discount(1, 33) == 0.67
    assert cart.apply_discount(99.99, 20) == 79.99

@pytest.mark.parametrize("price,percent", [
    (-10, 10),
    (100, -5),
    (100, 105)
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

@pytest.mark.parametrize("quantity,result", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),   # Expected to be 10 but implementation may return 5
    (99, 10),
    (100, 15),
    (200, 15)
])
def test_bulk_discount_percent(quantity, result):
    assert cart.bulk_discount_percent(quantity) == result

@pytest.mark.parametrize("quantity", [0, -5, 3.5, '10'])
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

valid_coupons = [
    ("SAVE10", 10),
    ("save20", 20),   # Case-insensitive
    (" SAVE5 ", 5),
    ("SaVe50", 50)
]
@pytest.mark.parametrize("code,percent", valid_coupons)
def test_parse_coupon_valid(code, percent):
    assert cart.parse_coupon(code) == percent

invalid_coupons = [
    "SAV10",
    "SAVE0",
    "SAVE51",
    "SAVE-5",
    "",
    123,
    "SAVE10SAVE20"
]
@pytest.mark.parametrize("code", invalid_coupons)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

@pytest.mark.parametrize("subtotal,member,expected", [
    (500, False, 60),
    (0, True, 30),
    (1000, False, 0),
    (1200, True, 0)
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

def test_shipping_fee_negative():
    with pytest.raises(ValueError):
        cart.shipping_fee(-1)

def test_cart_add_and_subtotal():
    c = cart.Cart()
    c.add_item("apple", 1.0, 3)
    assert c.items() == {"apple": 3}
    assert c.subtotal() == 3.0
    # Add same item again
    c.add_item("apple", 1.0, 2)
    assert c.items() == {"apple": 5}
    assert c.subtotal() == 5.0

def test_cart_add_different_price():
    c = cart.Cart()
    c.add_item("banana", 2.0, 1)
    with pytest.raises(ValueError):
        c.add_item("banana", 3.0, 1)

@pytest.mark.parametrize("price,quantity", [
    (-5, 1),
    (10, -2),
    (10, 0)
])
def test_cart_add_errors(price, quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("item", price, quantity)

def test_cart_remove_to_zero():
    c = cart.Cart()
    c.add_item("banana", 2.0, 5)
    c.remove_item("banana", 5)
    assert "banana" not in c.items()

def test_cart_remove_more_than_existing():
    c = cart.Cart()
    c.add_item("cherry", 3.0, 2)
    c.remove_item("cherry", 5)
    assert "cherry" not in c.items()

def test_cart_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent", 1)

def test_cart_subtotal_multiple_items():
    c = cart.Cart()
    c.add_item("apple", 1.0, 10)   # bulk discount 5%
    c.add_item("orange", 2.0, 5)
    assert c.subtotal() == 19.5

def test_cart_subtotal_empty():
    c = cart.Cart()
    assert c.subtotal() == 0

def test_cart_total_no_coupon_member():
    c = cart.Cart()
    c.add_item("item", 1050, 1)
    expected_shipping = cart.shipping_fee(1050, False)
    assert c.total(member=False) == round(1050 + expected_shipping, 2)

def test_cart_total_with_coupon_crossing_threshold():
    c = cart.Cart()
    c.add_item("big", 1050, 1)
    total = c.total(member=False, coupon="SAVE20")
    # Expected: discounted amount 840 + shipping fee 60 -> 900
    assert total == 900.0

def test_cart_total_with_coupon_crossing_threshold_member():
    c = cart.Cart()
    c.add_item("big", 1050, 1)
    total = c.total(member=True, coupon="SAVE20")
    # Expected: discounted amount 840 + shipping fee 30 -> 870
    assert total == 870.0

def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0
