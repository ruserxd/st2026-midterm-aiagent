import pytest
import cart

# apply_discount tests
@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),
    (123.456, 20, 98.76),   # round(123.456*80/100,2) = 98.76
    (100, 0, 100.0),
    (100, 100, 0.0)
])
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price,percent", [
    (-10, 20),     # negative price
    (100, -5),     # negative percent
    (100, 105)     # percent >100
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize("quantity,expected", [
    (9,0),
    (10,5),
    (49,5),
    (50,10),   # expected 10 per spec
    (51,10),
    (99,10),
    (100,15),
    (150,15)
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 2.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize("code,expected", [
    ("SAVE10",10),
    ("save20",20),          # case-insensitive
    ("  SAVE30  ",30),      # whitespace ignored
    ("SaVe05",5)            # case-insensitive mixed
])
def test_parse_coupon_valid_case_insensitive(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVEx","SAVE0","SAVE51","1234"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal,member,expected", [
    (100, False, 60),
    (999.99, False, 60),
    (1000, False, 0),
    (2000, True, 0),   # free shipping even for members
    (500, True, 30)
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1.5])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart class tests
def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item("apple", 1.5, quantity=2)
    assert c.items() == {"apple":2}
    c.add_item("apple", 1.5, quantity=3)
    assert c.items() == {"apple":5}

def test_cart_add_item_errors():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("bad", -1)   # negative unit price
    with pytest.raises(ValueError):
        c.add_item("bad", 1, quantity=0)
    with pytest.raises(ValueError):
        c.add_item("bad", 1, quantity=-3)
    with pytest.raises(ValueError):
        c.add_item("bad", 1, quantity=2.5)
    # unit price mismatch
    c.add_item("pear", 1.0, quantity=1)
    with pytest.raises(ValueError):
        c.add_item("pear", 2.0, quantity=1)

def test_cart_remove_item():
    c = cart.Cart()
    c.add_item("banana", 0.5, quantity=3)
    c.remove_item("banana", quantity=1)
    assert c.items() == {"banana":2}
    # Removing remaining items exactly should delete the entry per spec
    c.remove_item("banana", quantity=2)
    assert c.items() == {}   # expect empty dict; bug will keep key with 0

def test_cart_remove_more_than_quantity():
    c = cart.Cart()
    c.add_item("orange", 1.0, quantity=4)
    c.remove_item("orange", quantity=10)  # remove more than present
    assert c.items() == {}

def test_cart_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent")

def test_cart_items_copy_independent():
    c = cart.Cart()
    c.add_item("pear", 1.0, quantity=2)
    items_copy = c.items()
    items_copy['pear'] = 100
    assert c.items()['pear'] == 2   # original unchanged
    del items_copy['pear']
    assert 'pear' in c.items()     # still present

def test_cart_subtotal_empty():
    c = cart.Cart()
    assert c.subtotal() == 0

def test_cart_subtotal_no_discount():
    c = cart.Cart()
    c.add_item("widget", 10.5, quantity=3)
    assert c.subtotal() == 31.5

def test_cart_subtotal_bulk_discount():
    c = cart.Cart()
    c.add_item("gadget", 20.0, quantity=12)   # bulk discount 5%
    assert c.subtotal() == 228.0

def test_cart_subtotal_multiple_items_rounding():
    c = cart.Cart()
    c.add_item("widget", 10.5, quantity=3)    # 31.5
    c.add_item("gadget", 20.0, quantity=12)  # 228.0
    expected_total = round(31.5 + 228.0, 2)
    assert c.subtotal() == expected_total

def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0

def test_cart_total_no_coupon_non_member():
    c = cart.Cart()
    c.add_item("item", 30.0, quantity=1)
    assert c.total() == 90.0

def test_cart_total_no_coupon_member():
    c = cart.Cart()
    c.add_item("item", 30.0, quantity=1)
    assert c.total(member=True) == 60.0

def test_cart_total_with_coupon_non_member():
    c = cart.Cart()
    c.add_item("item", 100.0, quantity=1)
    assert c.total(coupon="SAVE10") == 150.0

def test_cart_total_with_coupon_member():
    c = cart.Cart()
    c.add_item("item", 100.0, quantity=1)
    assert c.total(member=True, coupon="SAVE10") == 120.0

def test_cart_total_bug_free_shipping_threshold_discount():
    c = cart.Cart()
    # Create subtotal just above threshold
    c.add_item("expensive", 203.0, quantity=5)   # subtotal 1015
    expected_total = round(507.5 + cart.shipping_fee(507.5), 2)  # shipping on discounted amount
    assert c.total(coupon="SAVE50") == expected_total

def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("item", 10.0, quantity=1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# Subtotal rounding bug test (per-line rounding vs spec) - this will reveal a mismatch
def test_cart_subtotal_rounding_per_line_bug():
    c = cart.Cart()
    # Two tiny items that individually are too small to survive rounding
    c.add_item("tiny1", 0.005, quantity=1)
    c.add_item("tiny2", 0.005, quantity=1)
    # Spec says subtotal is round(0.005 + 0.005, 2) -> 0.01
    assert c.subtotal() == 0.01
