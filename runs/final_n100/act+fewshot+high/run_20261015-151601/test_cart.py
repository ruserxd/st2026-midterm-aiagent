import pytest
import cart

# --------------------
# Helper functions for rounding and expected values
# --------------------

# Test apply_discount function

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price,percent", [
    (123.45, 0),   # zero percent -> unchanged
    (50, 100),     # full percent -> zero
])
def test_apply_discount_edge_cases(price, percent):
    expected = round(price * (1 - percent / 100), 2)
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price,percent", [
    (123.456, 10),     # rounding test
])
def test_apply_discount_rounding(price, percent):
    expected = round(price * (1 - percent / 100), 2)
    assert cart.apply_discount(price, percent) == pytest.approx(expected, rel=1e-9)

# Invalid inputs for apply_discount
@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_invalid_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# --------------------
# bulk_discount_percent tests
# --------------------

@pytest.mark.parametrize("quantity,expected", [
    (1, 0),   # below threshold
    (9, 0),   # just below 10
    (10, 5),  # exact 10
    (49, 5),  # below 50
    (50, 10), # exact 50
    (99, 10), # below 100
    (100, 15),# exact 100
    (150, 15),# above 100
])
def test_bulk_discount_percent_thresholds(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, -5])
def test_bulk_discount_percent_invalid_quantity_zero_or_negative(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# non-integer types should raise ValueError
@pytest.mark.parametrize("quantity", [3.5, "10", None])
def test_bulk_discount_percent_non_integer_type(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --------------------
# parse_coupon tests
# --------------------

@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save25", 25),
    (" SAVE50 ", 50),
])
def test_parse_coupon_valid_cases(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAV10",   # missing 'E'
    "SAVE0",   # below min N
    "SAVE51",  # above max N
    "12345",   # non-matching pattern
    "",        # empty string
])
def test_parse_coupon_invalid_cases(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --------------------
# shipping_fee tests
# --------------------

@pytest.mark.parametrize("subtotal,member,expected", [
    (999, False, 60),   # just below threshold
    (1000, False, 0),   # at threshold free
    (2000, False, 0),   # above threshold free
    (999, True, 30),    # member half fee
    (1000, True, 0),    # member still free
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_invalid_subtotal(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --------------------
# Cart class tests
# --------------------

# Helper to create a simple cart with items for later use

def _make_sample_cart():
    c = cart.Cart()
    c.add_item("apple", unit_price=1.5, quantity=3)
    c.add_item("banana", unit_price=0.75, quantity=12)  # discount threshold 10 -> 5%
    return c

def test_cart_initial_state():
    c = cart.Cart()
    assert isinstance(c.items(), dict)
    assert c.items() == {}

# Adding new item

def test_cart_add_item_new():
    c = cart.Cart()
    c.add_item("orange", unit_price=2.0, quantity=4)
    assert c.items() == {"orange": 4}

# Adding existing item with same price increments quantity

def test_cart_add_existing_same_price():
    c = cart.Cart()
    c.add_item("pear", unit_price=3.0, quantity=2)
    c.add_item("pear", unit_price=3.0, quantity=5)
    assert c.items() == {"pear": 7}

# Adding existing item with different price raises ValueError

def test_cart_add_existing_different_price():
    c = cart.Cart()
    c.add_item("kiwi", unit_price=1.0, quantity=3)
    with pytest.raises(ValueError):
        c.add_item("kiwi", unit_price=1.5, quantity=2)

# Removing items partially and fully

def test_cart_remove_partial_and_full():
    c = cart.Cart()
    c.add_item("grape", unit_price=0.4, quantity=5)
    # remove 3 -> remaining 2
    c.remove_item("grape", quantity=3)
    assert c.items() == {"grape": 2}
    # remove remaining 2 -> item removed entirely
    c.remove_item("grape", quantity=2)
    assert c.items() == {}

# Removing nonexistent item raises KeyError

def test_cart_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent", quantity=1)

# items() returns a copy; modifying the returned dict doesn't affect cart

def test_cart_items_copy_immutability():
    c = cart.Cart()
    c.add_item("mango", unit_price=2.5, quantity=6)
    items_copy = c.items()
    items_copy["mango"] = 100  # mutate copy
    assert c.items()["mango"] == 6

# Subtotal calculations

def test_cart_subtotal_no_discount():
    c = cart.Cart()
    c.add_item("tea", unit_price=5.0, quantity=4)
    assert c.subtotal() == pytest.approx(20.00, rel=1e-9)

# Subtotal with bulk discount applied to one item

def test_cart_subtotal_with_discount():
    c = cart.Cart()
    # 10 items => 5% discount
    c.add_item("coffee", unit_price=6.0, quantity=10)
    expected_amount = 6.0 * 10  # 60
    discounted = round(expected_amount * (1 - 0.05), 2)
    assert c.subtotal() == pytest.approx(discounted, rel=1e-9)

# Subtotal with multiple items and varying discounts

def test_cart_subtotal_multiple_items():
    c = cart.Cart()
    # item A: no discount (quantity 3)
    c.add_item("itemA", unit_price=10.0, quantity=3)  # subtotal 30
    # item B: 5% discount (quantity 12)
    c.add_item("itemB", unit_price=50.0, quantity=12)  # amount 600 -> discount 5% -> 570
    expected_total = round(10.0 * 3 + 50.0 * 12 * (1 - 0.05), 2)
    assert c.subtotal() == pytest.approx(expected_total, rel=1e-9)

# Total without coupon and non-member

def test_cart_total_no_coupon_non_member():
    c = cart.Cart()
    # 10 items => discount 5%
    c.add_item("widget", unit_price=20.0, quantity=10)  # discounted subtotal 190.0
    expected_subtotal = round(20.0 * 10 * (1 - 0.05), 2)
    shipping = cart.shipping_fee(expected_subtotal, member=False)
    total_expected = round(expected_subtotal + shipping, 2)
    assert c.total() == pytest.approx(total_expected, rel=1e-9)

# Total with coupon and non-member

def test_cart_total_with_coupon_non_member():
    c = cart.Cart()
    c.add_item("widget", unit_price=20.0, quantity=10)  # subtotal before discount 200
    # after bulk discount: 190
    expected_subtotal = round(20.0 * 10 * (1 - 0.05), 2)
    coupon_percent = cart.parse_coupon("SAVE10")
    discounted_amount = round(expected_subtotal * (1 - coupon_percent / 100), 2)
    shipping = cart.shipping_fee(discounted_amount, member=False)
    total_expected = round(discounted_amount + shipping, 2)
    assert c.total(coupon="SAVE10") == pytest.approx(total_expected, rel=1e-9)

# Total with coupon and member (half shipping if applicable)

def test_cart_total_with_coupon_member():
    c = cart.Cart()
    c.add_item("widget", unit_price=20.0, quantity=10)  # subtotal before discount 200
    expected_subtotal = round(20.0 * 10 * (1 - 0.05), 2)
    coupon_percent = cart.parse_coupon("SAVE10")
    discounted_amount = round(expected_subtotal * (1 - coupon_percent / 100), 2)
    shipping = cart.shipping_fee(discounted_amount, member=True)
    total_expected = round(discounted_amount + shipping, 2)
    assert c.total(member=True, coupon="SAVE10") == pytest.approx(total_expected, rel=1e-9)

# Total with no items (empty cart) should be zero regardless of options

def test_cart_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0
    assert c.total(member=True) == 0
    assert c.total(coupon="SAVE10") == 0
    assert c.total(member=True, coupon="SAVE20") == 0

# Total with invalid coupon raises ValueError

def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("item", unit_price=1.0, quantity=2)
    with pytest.raises(ValueError):
        c.total(coupon="SAV20")  # missing 'E'

# Edge case: items with zero price, shipping should still apply if cart not empty

def test_cart_total_zero_price_items():
    c = cart.Cart()
    c.add_item("freeitem", unit_price=0.0, quantity=5)
    # subtotal is 0, after bulk discount remains 0
    expected_subtotal = round(0.0 * 5 * (1 - 0), 2)  # 0.0
    shipping = cart.shipping_fee(expected_subtotal, member=False)
    total_expected = round(expected_subtotal + shipping, 2)
    assert c.total() == pytest.approx(total_expected, rel=1e-9)

# Edge case: coupon that pushes discounted subtotal over free threshold

def test_cart_total_discount_pushing_over_threshold():
    # Create cart with subtotal just below 1000 before discount
    c = cart.Cart()
    # Add items to reach e.g., 1050 total, then apply large coupon
    c.add_item("expensive", unit_price=300.0, quantity=4)  # 1200
    # After bulk discount? quantity 4 <10 -> no discount => subtotal 1200 >1000 free shipping
    assert c.total() == pytest.approx(1200.0, rel=1e-9)
    # Apply a coupon that reduces it below threshold; shipping should be added now
    c2 = cart.Cart()
    c2.add_item("expensive", unit_price=300.0, quantity=4)
    discounted_subtotal = round(1200 * (1 - cart.parse_coupon("SAVE10") / 100), 2)  # 1080
    shipping_after_coupon = cart.shipping_fee(discounted_subtotal, member=False)
    expected_total = round(discounted_subtotal + shipping_after_coupon, 2)
    assert c2.total(coupon="SAVE10") == pytest.approx(expected_total, rel=1e-9)
