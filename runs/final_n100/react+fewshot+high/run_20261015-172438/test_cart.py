import pytest
import cart

# ---------- apply_discount -------------------------------------------------
def test_apply_discount_valid_cases():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(100, 100) == 0.0
    # Test rounding to two decimals
    assert cart.apply_discount(99.999, 10) == round(99.999 * 0.9, 2)

def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        cart.apply_discount(-5, 10)

def test_apply_discount_invalid_percent():
    for bad in (-1, 101, 200):
        with pytest.raises(ValueError):
            cart.apply_discount(100, bad)

# ---------- bulk_discount_percent -----------------------------------------
def test_bulk_discount_percent_boundaries():
    # Valid boundaries
    assert cart.bulk_discount_percent(10) == 5   # quantity >=10 => 5%
    assert cart.bulk_discount_percent(50) == 10  # quantity >=50 => 10%
    assert cart.bulk_discount_percent(100) == 15

def test_bulk_discount_percent_invalid():
    for bad in (-5, 0, "ten"):
        with pytest.raises(ValueError):
            cart.bulk_discount_percent(bad)

# ---------- parse_coupon ---------------------------------------------------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save25", 25),   # case-insensitive
    ("   Save50   ", 50),  # whitespace trimmed
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVE0",
    "SAVE51",
    "SAVEXY",
    "100",
    "",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------------------------------------------------
def test_shipping_fee_non_member():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0

def test_shipping_fee_member():
    assert cart.shipping_fee(0, member=True) == 30
    assert cart.shipping_fee(999.99, member=True) == 30

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ------------------------------------------------------
def test_cart_initial_state():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item("apple", 100, 2)
    c.add_item("banana", 50)
    # Adding an existing item with same price increases quantity
    c.add_item("apple", 100, 3)
    assert c.items() == {"apple": 5, "banana": 1}

def test_cart_add_invalid():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("pear", -10, 1)   # negative price
    with pytest.raises(ValueError):
        c.add_item("pear", 10, 0)   # zero quantity
    c.add_item("pear", 10, 2)
    with pytest.raises(ValueError):
        c.add_item("pear", 12, 1)   # price mismatch

def test_cart_remove_and_items():
    c = cart.Cart()
    c.add_item("orange", 30, 5)
    c.remove_item("orange", 2)
    assert c.items() == {"orange": 3}
    # Removing more than existing removes the item
    c.remove_item("orange", 5)
    assert c.items() == {}
    with pytest.raises(KeyError):
        c.remove_item("orange", 1)

def test_cart_subtotal_with_bulk_discounts():
    c = cart.Cart()
    # 10 units -> 5% discount
    c.add_item("pen", 20, 10)   # subtotal before discount: 200
    assert c.subtotal() == round(200 * 0.95, 2)
    # 50 units -> 10% discount (but implementation bug gives 5%)
    c.add_item("notebook", 5, 50)  # 250 before discount
    expected = round(200 * 0.95 + 250 * 0.90, 2)
    assert c.subtotal() == expected
    # 100 units -> 15% discount
    c.add_item("marker", 1, 100)  # 100 before discount
    expected += round(100 * 0.85, 2)
    assert c.subtotal() == expected

def test_cart_total_no_coupon_or_member():
    c = cart.Cart()
    c.add_item("item", 200, 1)   # subtotal 200
    total = c.total()
    # subtotal + shipping (shipping is 60 because <1000)
    expected = round(200 + 60, 2)
    assert total == expected

def test_cart_total_with_member_and_coupon():
    c = cart.Cart()
    c.add_item("item", 500, 3)   # 1500 before discounts
    # bulk discount: quantity=3 -> none
    subtotal_before = 1500.00
    # Apply coupon SAVE20 (20%) via apply_discount
    total_after_coupon = cart.apply_discount(subtotal_before, 20)
    # Shipping on subtotal after coupon: 1500*0.8=1200 >=1000 => free shipping
    expected_total = round(total_after_coupon + 0, 2)
    assert c.total(member=True, coupon="SAVE20") == expected_total

def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("item", 10, 1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

def test_cart_total_empty_no_shipping():
    c = cart.Cart()
    assert c.total() == 0

# ---------- Shipping fee bug due to total implementation --------------------
def test_total_coupon_affects_shipping_fee_bug():
    # Subtotal exactly 1000 -> free shipping normally
    c = cart.Cart()
    c.add_item("item", 200, 5)   # subtotal 1000
    # Coupon reduces subtotal to below 1000
    expected_after_discount = cart.apply_discount(1000, 20)   # 800
    expected_total_non_member = round(expected_after_discount + 60, 2)   # 860
    assert c.total(coupon="SAVE20") == expected_total_non_member

def test_total_coupon_affects_shipping_fee_bug_member():
    c = cart.Cart()
    c.add_item("item", 200, 5)   # subtotal 1000
    expected_after_discount = cart.apply_discount(1000, 20)   # 800
    expected_total_member = round(expected_after_discount + 30, 2)   # 830
    assert c.total(member=True, coupon="SAVE20") == expected_total_member
