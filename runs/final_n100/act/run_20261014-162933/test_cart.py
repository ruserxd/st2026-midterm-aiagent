import cart
import pytest

# ---- helper functions for creating carts with items

def make_cart_with_items(items):
    c = cart.Cart()
    for name, unit_price, quantity in items:
        c.add_item(name, unit_price, quantity)
    return c

# ---------- parse_coupon tests ----------

@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save10", 10),
    (" SAVE10 ", 10),
    ("Save50", 50),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("invalid_code", [
    "",          # empty string
    "SAVE",      # no number
    "SAVEX0",    # zero not allowed
    "save51",    # >50
    "save-5",    # negative
    "ABCD10",    # wrong prefix
    " SAVE10X ",# trailing characters
])
def test_parse_coupon_invalid(invalid_code):
    with pytest.raises(ValueError):
        cart.parse_coupon(invalid_code)

# ---------- shipping_fee tests ----------

@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (500, True, 30),
    (999.99, False, 60),
    (1000, False, 0),
    (1500, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -0.01])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- bulk_discount_percent tests ----------

@pytest.mark.parametrize("qty,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (250, 15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("invalid_qty", [0, -5, -1.2, '10'])
def test_bulk_discount_percent_invalid(invalid_qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(invalid_qty)

# ---------- apply_discount tests ----------

@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 10, 90.0),
    (50, 0, 50.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [
    (-1, 10),
    (10, -5),
    (10, 150),
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- Cart class tests ----------

def test_cart_empty_total():
    c = cart.Cart()
    assert c.subtotal() == 0
    assert c.total() == 0
    assert c.items() == {}

# add and remove items

def test_cart_add_remove_items():
    c = cart.Cart()
    c.add_item('apple', 2, 3)
    c.add_item('banana', 1.5)
    # subtotal should be 3*2 + 1*1.5 = 6 + 1.5 = 7.5
    assert c.subtotal() == 7.5
    assert c.items()['apple'] == {'unit_price': 2, 'quantity': 3}
    assert c.items()['banana'] == {'unit_price': 1.5, 'quantity': 1}

    # remove one banana
    c.remove_item('banana')
    assert 'banana' not in c.items()

    # remove two apples -> should delete key
    c.remove_item('apple', quantity=2)
    assert c.items()['apple']['quantity'] == 1

# total with member and coupon

def test_cart_total_with_member_and_coupon():
    c = cart.Cart()
    c.add_item('widget', 200, 5)   # subtotal 1000
    # No shipping because >= 1000
    assert c.total(member=True, coupon='save10') == 900.0
    # Applying coupon first: 1000 - 10% = 900; then no shipping -> 900

# total with coupon only

def test_cart_total_with_coupon_only():
    c = cart.Cart()
    c.add_item('gadget', 120, 1)   # subtotal 120
    # apply 20% coupon (invalid should raise ValueError)
    with pytest.raises(ValueError):
        c.total(coupon='save60')

# total with shipping after discount

def test_cart_total_shipping_after_discount():
    c = cart.Cart()
    c.add_item('book', 40, 3)      # subtotal 120
    # 10% coupon -> 108; shipping fee for 108 is 60 (non-member)
    assert c.total(coupon='save10') == 168.0

# total with member no shipping

def test_cart_total_member_no_shipping():
    c = cart.Cart()
    c.add_item('expensive', 1100, 1)
    # subtotal 1100, member => free shipping
    assert c.total(member=True) == 1100.0

# bulk discount logic inside Cart? not defined but test assumption that no bulk discounts applied

if __name__ == '__main__':
    pytest.main()
