import pytest
import cart

# -------------------- Utility helpers for test expectations --------------------

# Helper to round to two decimals, matching cart's behaviour
round2 = lambda x: round(x + 1e-12, 2)  # avoid floating point quirks

# -------------------- Tests for standalone functions --------------------

@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),            # example from spec
    (100, 0, 100.0),             # no discount
    (50, 100, 0.0),              # full discount
])
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# invalid price / percent
@pytest.mark.parametrize("price,percent", [
    (-10, 10),      # negative price
    (50, -5),       # negative percent
    (50, 105),      # percent >100
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),     # below 10
    (10, 5),    # at 10
    (49, 5),    # just below 50
    (50, 10),   # at 50
    (99, 10),   # just below 100
    (100, 15),  # at 100
    (150, 15),  # above 100
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# invalid quantity
@pytest.mark.parametrize("quantity", [0, -5, 3.2, "10"])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", [
    "SAVE0",          # below 1
    "SAVE51",         # above 50
    "INVALID",        # wrong prefix
    "SAVEX10",        # malformed numeric part
    "   ",            # empty after strip
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal,expected", [
    (0, 60),          # below free threshold
    (999.99, 60),     # just below 1000
    (1000, 0),        # exactly free
    (1500, 0),        # above free
])
def test_shipping_fee_regular(subtotal, expected):
    assert cart.shipping_fee(subtotal) == expected

# member pays half
@pytest.mark.parametrize("subtotal,expected", [
    (500, 30),
    (1000, 0),  # free regardless of membership
])
def test_shipping_fee_member(subtotal, expected):
    assert cart.shipping_fee(subtotal, member=True) == expected

# invalid subtotal
@pytest.mark.parametrize("subtotal", [-10, -1.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# -------------------- Tests for Cart class --------------------

def test_cart_initially_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 0.0

# adding items and verifying quantity & price consistency

def test_add_item_increases_quantity_and_total():
    c = cart.Cart()
    c.add_item("Apple", unit_price=5.0)
    assert c.items() == {"Apple": 1}
    assert c.subtotal() == round2(5.0)   # no bulk discount
    assert c.total() == round2(5.0 + cart.shipping_fee(5.0))

    # Add same item again with same unit price
    c.add_item("Apple", unit_price=5.0, quantity=3)
    assert c.items() == {"Apple": 4}
    # subtotal: 4 * 5 = 20, still <10 => no discount
    assert c.subtotal() == round2(20.0)
    # shipping on 20
    expected_total = round2(20.0 + cart.shipping_fee(20.0))
    assert c.total() == expected_total

    # add a different item with larger quantity to trigger bulk discount
    c.add_item("Banana", unit_price=2.0, quantity=10)
    # Banana subtotal before discount: 20
    # bulk_discount_percent(10) => 5%
    banana_sub = round2(20 * (1 - 0.05))
    expected_subtotal = round2(20.0 + banana_sub)
    assert c.subtotal() == expected_subtotal

# attempting to add item with different unit price raises ValueError

def test_add_item_price_mismatch():
    c = cart.Cart()
    c.add_item("Apple", unit_price=5.0)
    with pytest.raises(ValueError):
        c.add_item("Apple", unit_price=6.0)

# invalid unit price or quantity
@pytest.mark.parametrize("unit_price,quantity", [(-1, 1), (2, 0), (3, -2)])
def test_add_item_invalid(unit_price, quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("Item", unit_price=unit_price, quantity=quantity)

# removing items and auto-removal when quantity reaches zero

def test_remove_item():
    c = cart.Cart()
    c.add_item("Apple", 5.0, quantity=3)
    c.remove_item("Apple", quantity=1)
    assert c.items() == {"Apple": 2}
    c.remove_item("Apple", quantity=2)   # should remove completely
    assert c.items() == {}

# removing non-existent item raises KeyError

def test_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("NonExistent")

# total calculations with coupon and shipping logic

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    # Add items to exceed 1000 subtotal after discount removal
    c.add_item("Expensive", unit_price=200.0, quantity=6)  # 1200 before discounts
    # No bulk discount for 6 units (below 10)
    subtotal_before_coupon = round2(1200.0)
    # Apply a valid coupon 'SAVE20' => 20%
    amount_after_coupon = round2(subtotal_before_coupon * (1 - 0.20))
    shipping = cart.shipping_fee(amount_after_coupon)  # should be 60 because <1000
    expected_total = round2(amount_after_coupon + shipping)
    assert c.total(coupon="SAVE20") == expected_total

# total with member flag affecting shipping only if fee applies

def test_member_shipping_free_when_no_fee():
    c = cart.Cart()
    c.add_item("Expensive", unit_price=200.0, quantity=5)  # subtotal 1000 exactly
    assert c.total(member=True) == round2(1000.0)  # shipping free regardless of member flag

# invalid coupon raises ValueError

def test_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("Apple", 5.0)
    with pytest.raises(ValueError):
        c.total(coupon="BAD")

# empty cart total is zero, no shipping charged

def test_empty_cart_total_zero():
    c = cart.Cart()
    assert c.total() == 0.0
