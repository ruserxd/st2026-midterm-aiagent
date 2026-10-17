import pytest
import cart

# ---------- Apply Discount Tests ----------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(100, 100) == 0.0
    # rounding to two decimal places
    assert cart.apply_discount(10, 33) == round(10 * (100 - 33) / 100, 2)

@pytest.mark.parametrize("price,percent", [
    (200, -1),
    (200, 101),
])
def test_apply_discount_invalid_percent(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

def test_apply_discount_negative_price():
    with pytest.raises(ValueError):
        cart.apply_discount(-10, 50)

# ---------- Bulk Discount Percent Tests ----------

@pytest.mark.parametrize("quantity,expected", [
    (5, 0),
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),   # spec: >= 50 gives 10%, implementation erroneously returns 5%
    (51, 10),
    (99, 10),
    (100, 15),
    (101, 15),
])
def test_bulk_discount_percent_valid(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 3.7, "10"])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- Parse Coupon Tests ----------

@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save25", 25),   # spec: case‑insensitive but implementation is case‑sensitive
    (" SAVE50 ", 50),
    ("SaVe1", 1),     # spec: case‑insensitive
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVE0",
    "SAVE51",
    "SALE10",
    "",
    "SAVEABC",
    123,
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- Shipping Fee Tests ----------

@pytest.mark.parametrize("subtotal,member,expected", [
    (1000, False, 0),
    (1000, True, 0),
    (999.99, False, 60),
    (999.99, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart Class Tests ----------

def test_cart_initially_empty():
    c = cart.Cart()
    assert c.items() == {}

def test_cart_add_item_new_and_existing_same_price():
    c = cart.Cart()
    c.add_item('apple', 1.5, 3)
    assert c.items()['apple'] == 3
    # add same item with the same unit price
    c.add_item('apple', 1.5, 2)
    assert c.items()['apple'] == 5

def test_cart_add_item_different_price_error():
    c = cart.Cart()
    c.add_item('orange', 0.5, 1)
    with pytest.raises(ValueError):
        c.add_item('orange', 0.6, 1)

def test_cart_add_invalid_parameters():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item('bad', -1.0, 1)
    with pytest.raises(ValueError):
        c.add_item('bad', 1.0, 0)
    with pytest.raises(ValueError):
        c.add_item('bad', 1.0, -3)

def test_cart_remove_item_partial_and_total():
    c = cart.Cart()
    c.add_item('banana', 0.2, 4)
    c.remove_item('banana', 1)
    assert c.items()['banana'] == 3

def test_cart_remove_item_all_removes_entry():
    c = cart.Cart()
    c.add_item('pear', 5.0, 2)
    c.remove_item('pear', 2)  # quantity becomes zero – spec requires removal
    assert 'pear' not in c.items()  # this will fail if the implementation leaves a zero entry

def test_cart_remove_nonexistent_raises_keyerror():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item('nonexistent')

# ---------- Subtotal Tests ----------

def test_cart_subtotal_with_bulk_discount():
    c = cart.Cart()
    # item without bulk discount
    c.add_item('apple', 10.0, 5)
    # item with a 5% bulk discount (quantity 15)
    c.add_item('banana', 2.0, 15)
    expected_line1 = round(10 * 5 * (100 - 0) / 100, 2)   # 50.00
    expected_line2 = round(2 * 15 * (100 - 5) / 100, 2)   # 28.50
    assert c.subtotal() == round(expected_line1 + expected_line2, 2)

# ---------- Total Tests ----------

def test_cart_total_no_coupon_non_member():
    c = cart.Cart()
    c.add_item('item', 200.0, 3)  # subtotal 600
    expected_total = round(600 + 60, 2)
    assert c.total() == expected_total

@pytest.mark.parametrize("member", [False, True])
def test_cart_total_no_coupon_member_flag(member):
    c = cart.Cart()
    c.add_item('item', 200.0, 3)  # subtotal 600
    shipping_fee_expected = 30 if member else 60
    expected_total = round(600 + shipping_fee_expected, 2)
    assert c.total(member=member) == expected_total

def test_cart_total_coupon_below_threshold():
    c = cart.Cart()
    c.add_item('expensive', 200.0, 6)  # subtotal 1200
    # coupon 50% -> discounted amount 600; shipping on discounted amount should be 60
    expected_total_non_member = round(600 + 60, 2)
    assert c.total(coupon="SAVE50") == expected_total_non_member

def test_cart_total_coupon_below_threshold_with_member():
    c = cart.Cart()
    c.add_item('expensive', 200.0, 6)  # subtotal 1200
    expected_total_member = round(600 + 30, 2)
    assert c.total(member=True, coupon="SAVE50") == expected_total_member

def test_cart_total_invalid_coupon_raises():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.total(coupon="BAD10")

def test_cart_total_empty_cart_zero():
    c = cart.Cart()
    assert c.total() == 0
