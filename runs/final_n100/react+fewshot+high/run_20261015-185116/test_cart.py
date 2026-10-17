import pytest
import cart

# ---------- Tests for apply_discount ----------
@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),          # standard case
    (19.99, 12, 17.59),       # rounding check
    (50, 100, 0.0),           # 100% discount
    (10, 0, 10.0)              # zero percent discount
])
def test_apply_discount_valid_cases(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price,percent", [
    (-1, 10),                 # negative price
    (-5, 50)
])
def test_apply_discount_invalid_price(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

@pytest.mark.parametrize("price,percent", [
    (100, -5),                 # negative percent
    (100, 105),                # percent > 100
    (200, 200),                # far above max
    (0, -1)                    # zero price but negative percent
])
def test_apply_discount_invalid_percent(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- Tests for bulk_discount_percent ----------
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),                    # below first threshold
    (10, 5),                   # at 10
    (49, 5),                   # just below 50
    (50, 10),                  # at 50
    (99, 10),                  # just below 100
    (100, 15),                 # at 100
    (150, 15)                  # above highest threshold
])
def test_bulk_discount_percent_boundary(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, -5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- Tests for parse_coupon ----------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),          # simple case
    ("save20", 20),           # lower‑case
    (" SAVE30 ", 30),         # whitespace trimming
    ("SaVe1", 1),             # mixed case and small number
    ("saVE50", 50)            # maximum allowed
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAV10",                # missing 'E'
    "save0",                 # zero percent not allowed
    "save51",                # above max 50
    "sav e10",               # internal whitespace
    "",                       # empty string
    "   ",                   # only spaces
    "  SAVE-5  ",            # negative number
    "SAVEabc"                 # non‑numeric suffix
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- Tests for shipping_fee ----------
@pytest.mark.parametrize("subtotal,member,expected", [
    (1000, False, 0),          # exactly free threshold
    (1500, True, 0),           # above threshold, member
    (999.99, False, 60),       # just below threshold, non‑member
    (500, True, 30),           # lower subtotal, member
    (0, False, 60),            # zero subtotal, non‑member
    (0, True, 30)              # zero subtotal, member
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10, -0.01])
def test_shipping_fee_negative_subtotal_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Tests for Cart class methods ----------

def test_cart_add_item_basic():
    c = cart.Cart()
    c.add_item('apple', unit_price=1.00, quantity=3)
    assert c.items() == {'apple': 3}
    assert c.subtotal() == 3.0

def test_cart_add_item_negative_price():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item('banana', unit_price=-5.00, quantity=1)

def test_cart_add_item_zero_quantity():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item('orange', unit_price=2.0, quantity=0)

def test_cart_add_same_item_increase_quantity():
    c = cart.Cart()
    c.add_item('apple', unit_price=1.00, quantity=2)
    c.add_item('apple', unit_price=1.00, quantity=3)
    assert c.items() == {'apple': 5}
    assert c.subtotal() == 5.0

def test_cart_add_same_item_different_price_raises():
    c = cart.Cart()
    c.add_item('apple', unit_price=1.00, quantity=2)
    with pytest.raises(ValueError):
        c.add_item('apple', unit_price=1.50, quantity=1)

def test_cart_items_returns_copy():
    c = cart.Cart()
    c.add_item('apple', unit_price=1.0, quantity=2)
    items_copy = c.items()
    items_copy['apple'] = 999
    assert c.items()['apple'] == 2

def test_cart_remove_partial_and_complete():
    c = cart.Cart()
    c.add_item('apple', unit_price=1.0, quantity=5)
    c.remove_item('apple', quantity=2)
    assert c.items() == {'apple': 3}
    assert c.subtotal() == 3.0
    # remove more than remaining to trigger removal of item
    c.remove_item('apple', quantity=5)
    assert c.items() == {}

def test_cart_remove_nonexistent_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item('pear', quantity=1)

# ---------- Tests for Cart.subtotal ----------

def test_cart_subtotal_single_no_discount():
    c = cart.Cart()
    c.add_item('apple', unit_price=3.0, quantity=5)   # qty < 10
    assert c.subtotal() == 15.0

def test_cart_subtotal_bulk_discounts():
    c = cart.Cart()
    # Apple: qty 10 -> 5% discount
    c.add_item('apple', unit_price=1.00, quantity=10)
    # Banana: qty 50 -> 10% discount
    c.add_item('banana', unit_price=2.50, quantity=50)
    expected_subtotal = round(9.5 + 112.5, 2)   # 122.0
    assert c.subtotal() == expected_subtotal

def test_cart_subtotal_multiple_discounts():
    c = cart.Cart()
    c.add_item('apple', unit_price=1.99, quantity=12)
    c.add_item('banana', unit_price=3.00, quantity=50)
    c.add_item('cherry', unit_price=5.00, quantity=120)
    line_apple = round(1.99 * 12 * (1 - 0.05), 2)   # 22.69
    line_banana = round(3.0 * 50 * (1 - 0.10), 2)    # 135.0
    line_cherry = round(5.0 * 120 * (1 - 0.15), 2)   # 510.0
    expected_subtotal = round(line_apple + line_banana + line_cherry, 2)
    assert c.subtotal() == expected_subtotal

def test_cart_subtotal_empty():
    c = cart.Cart()
    assert c.subtotal() == 0

# ---------- Tests for Cart.total ----------

def test_cart_total_no_coupon_non_member_below_threshold():
    c = cart.Cart()
    c.add_item('apple', unit_price=1.00, quantity=5)
    subtotal_expected = round(5.0 * (1 - 0), 2)   # 5.0
    shipping_fee_val = 60
    total_expected = round(subtotal_expected + shipping_fee_val, 2)
    assert c.total() == total_expected

def test_cart_total_no_coupon_member_below_threshold():
    c = cart.Cart()
    c.add_item('apple', unit_price=1.00, quantity=5)
    subtotal_expected = round(5.0 * (1 - 0), 2)   # 5.0
    shipping_fee_val = 30
    total_expected = round(subtotal_expected + shipping_fee_val, 2)
    assert c.total(member=True) == total_expected

def test_cart_total_no_coupon_above_threshold():
    c = cart.Cart()
    c.add_item('expensive', unit_price=200.0, quantity=6)
    subtotal_expected = round(200.0 * 6 * (1 - 0), 2)   # 1200.0
    shipping_fee_val = 0
    total_expected = round(subtotal_expected + shipping_fee_val, 2)
    assert c.total() == total_expected

def test_cart_total_with_coupon_and_member():
    c = cart.Cart()
    c.add_item('apple', unit_price=1.00, quantity=10)   # subtotal after bulk discount: 9.5
    coupon_percent = 20
    amount_after_discount = round(9.5 * (1 - coupon_percent / 100), 2)
    shipping_fee_val = cart.shipping_fee(amount_after_discount, member=True)
    total_expected = round(amount_after_discount + shipping_fee_val, 2)
    assert c.total(member=True, coupon="SAVE20") == total_expected

def test_cart_total_with_coupon_non_member():
    c = cart.Cart()
    c.add_item('apple', unit_price=1.00, quantity=10)   # subtotal after bulk discount: 9.5
    coupon_percent = 20
    amount_after_discount = round(9.5 * (1 - coupon_percent / 100), 2)
    shipping_fee_val = cart.shipping_fee(amount_after_discount, member=False)
    total_expected = round(amount_after_discount + shipping_fee_val, 2)
    assert c.total(coupon="SAVE20") == total_expected

def test_cart_total_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item('apple', unit_price=1.00, quantity=5)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")

def test_cart_total_empty_cart_zero_cost():
    c = cart.Cart()
    assert c.total() == 0
    assert c.total(member=True) == 0

def test_cart_total_empty_with_valid_coupon_returns_zero():
    c = cart.Cart()
    assert c.total(coupon="SAVE20") == 0

def test_cart_total_empty_invalid_coupon_raises():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
