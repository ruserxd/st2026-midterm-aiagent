import pytest
import cart

# --- standalone functions ---

@pytest.mark.parametrize("price, percent, expected", [
    (200, 15, 170.0),          # example from spec
    (100, 0, 100.0),           # no discount
    (50, 100, 0.0),            # full discount
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price, percent", [
    (-1, 10),          # negative price
    (100, -5),         # percent < 0
    (100, 105),        # percent > 100
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

@pytest.mark.parametrize("quantity, expected", [
    (9, 0),      # below 10
    (10, 5),     # 10-49
    (50, 10),    # 50-99
    (100, 15),   # 100+ 
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 3.2])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize("code, expected", [
    ("SAVE10", 10),
    (" save20 ", 20),   # case-insensitive and whitespace
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVEXX",      # non-integer
    "SAVE0",       # below 1
    "SAVE51",      # above 50
    "INVALID",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal, member, expected", [
    (1200, False, 0),      # free above 1000
    (999, True, 30),       # member gets half
    (999, False, 60),      # non-member
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart class tests

def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item("apple", 2.0, 3)
    assert c.items() == {"apple": 3}
    # adding same item increases quantity
    c.add_item("apple", 2.0, 2)
    assert c.items() == {"apple": 5}
    # different unit price raises ValueError
    with pytest.raises(ValueError):
        c.add_item("apple", 3.0, 1)

@pytest.mark.parametrize("name, quantity", [
    ("banana", 2),
])
def test_cart_remove_item(name, quantity):
    c = cart.Cart()
    c.add_item(name, 1.5, 5)
    c.remove_item(name, 2)
    assert c.items() == {name: 3}
    # remove more than existing removes item
    c.remove_item(name, 3)
    assert name not in c.items()

def test_cart_remove_missing():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent", 1)

# subtotal and total calculations

def test_subtotal_and_total_without_discounts():
    c = cart.Cart()
    c.add_item("widget", 10.0, 5)   # quantity <10 => no bulk discount
    assert c.subtotal() == 50.00
    assert c.total() == 110.00   # 50 + shipping 60 (non-member)

def test_subtotal_with_bulk_discount():
    c = cart.Cart()
    c.add_item("gadget", 20.0, 12)   # bulk discount 5%
    # expected item total: 20*12=240 -> minus 5% => 228.00
    assert c.subtotal() == 228.00
    assert c.total() == 288.00      # + shipping 60

def test_total_with_coupon_and_member():
    c = cart.Cart()
    c.add_item("thing", 100.0, 10)   # bulk discount 5% -> 950.00
    total_before = c.subtotal()      # 950.00
    assert total_before == 950.00
    # apply coupon SAVE10 => 10% off subtotal -> 855.00
    # shipping fee for non-member on 855 is 60 => 915.00
    assert c.total(member=False, coupon="SAVE10") == 915.00
    # member pays half shipping: 30 => 885.00
    assert c.total(member=True, coupon="SAVE10") == 885.00

# empty cart total should be 0

def test_empty_cart_total():
    c = cart.Cart()
    assert c.total() == 0
