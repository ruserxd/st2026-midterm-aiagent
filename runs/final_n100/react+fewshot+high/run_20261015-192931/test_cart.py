import pytest
import cart

# ---------------------------------------------------------------------------
# apply_discount
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),
        (150, 0, 150.0),
        (50, 100, 0.0),
        (99.99, 33, 66.99),
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price,percent",
    [(-10, 20), (100, -5), (100, 105)],
)
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------------------------------------------------------------------------
# bulk_discount_percent
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -5, 3.5],
)
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------------------------------------------------------------------------
# parse_coupon
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        (" save20 ", 20),
        ("SaVe30", 30),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "DISCOUNT5",
        "SAVE0",
        "SAVE51",
        "SAVExx",
        "SAVE10.5",
        "",
        "   ",
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------------------------------------------------------------------------
# shipping_fee
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (1000, False, 0),
        (999.99, False, 60),
        (500, False, 60),
        (500, True, 30),
        (2000, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-1, -100],
)
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------------------------------------------------------------------------
# Cart class
# ---------------------------------------------------------------------------
def test_cart_initial_state():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0

# ---------------------------------------------------------------------------
# add_item
# ---------------------------------------------------------------------------
def test_cart_add_item():
    c = cart.Cart()
    c.add_item("apple", 1.00, 5)
    assert c.items() == {"apple": 5}
    # Adding the same item increases quantity
    c.add_item("apple", 1.00, 3)
    assert c.items() == {"apple": 8}
    # Different unit price for existing item raises ValueError
    with pytest.raises(ValueError):
        c.add_item("apple", 2.00, 1)
    # Negative unit price or zero quantity raise ValueError
    with pytest.raises(ValueError):
        c.add_item("orange", -1.0, 2)
    with pytest.raises(ValueError):
        c.add_item("banana", 1.0, 0)

# ---------------------------------------------------------------------------
# remove_item
# ---------------------------------------------------------------------------
def test_cart_remove_item():
    c = cart.Cart()
    c.add_item("apple", 1.00, 8)
    c.remove_item("apple", 3)
    assert c.items() == {"apple": 5}
    # Removing the remaining quantity removes the item entirely
    c.remove_item("apple", 5)
    assert c.items() == {}
    # Removing more than present does not raise an error and removes the item
    c.add_item("banana", 1.0, 4)
    c.remove_item("banana", 10)
    assert "banana" not in c.items()
    # Removing a non‑existent item raises KeyError
    with pytest.raises(KeyError):
        c.remove_item("cherry", 1)

# ---------------------------------------------------------------------------
# items copy semantics
# ---------------------------------------------------------------------------
def test_cart_items_copy():
    c = cart.Cart()
    c.add_item("apple", 1.00, 7)
    items_copy = c.items()
    # Mutating the returned dict should not affect the cart's internal state
    items_copy["apple"] = 999
    assert c.items()["apple"] == 7

# ---------------------------------------------------------------------------
# subtotal calculations
# ---------------------------------------------------------------------------
def test_cart_subtotal_empty():
    c = cart.Cart()
    assert c.subtotal() == 0

def test_cart_subtotal_single_no_discount():
    c = cart.Cart()
    c.add_item("tshirt", 20.00, 2)
    assert c.subtotal() == 40.0

def test_cart_subtotal_single_with_discount():
    c = cart.Cart()
    c.add_item("hat", 10.00, 12)  # bulk discount 5%
    expected = round(10.00 * 12 * (1 - 0.05), 2)
    assert c.subtotal() == expected

def test_cart_subtotal_multiple_items():
    c = cart.Cart()
    c.add_item("apple", 2.00, 15)   # bulk discount 5%
    c.add_item("banana", 1.50, 55)  # bulk discount 10%
    raw_total = (2.00 * 15) * (1 - 0.05) + (1.50 * 55) * (1 - 0.10)
    expected = round(raw_total, 2)
    assert c.subtotal() == expected

def test_cart_subtotal_rounding_difference():
    c = cart.Cart()
    # Two items that produce discounted amounts requiring rounding difference
    c.add_item("itemA", 1.11, 10)   # bulk discount 5%
    c.add_item("itemB", 1.11, 10)   # same quantity and price
    expected = round(((1.11 * 10) * (1 - 0.05)) * 2, 2)
    assert c.subtotal() == expected

# ---------------------------------------------------------------------------
# total calculations
# ---------------------------------------------------------------------------
def test_cart_total_empty_non_member_no_coupon():
    c = cart.Cart()
    # An empty cart costs 0 (no shipping is charged).
    assert c.total(member=False) == 0

# Test that a large non‑member order with free shipping and a coupon works.
# ---------------------------------------------------------------------------
def test_cart_total_shipping_free_and_coupon():
    c = cart.Cart()
    c.add_item("apple", 200.00, 3)
    c.add_item("banana", 500.00, 2)
    base_total = 1600 + cart.shipping_fee(1600)  # shipping fee is 0
    expected = round(cart.apply_discount(base_total, 10), 2)
    assert c.total(member=False, coupon="SAVE10") == expected

# Test member order with coupon where shipping is computed after discount.
# ---------------------------------------------------------------------------
def test_cart_total_member_shipping_and_coupon():
    c = cart.Cart()
    c.add_item("apple", 200.00, 1)
    # subtotal before discount
    subtotal = 200.0
    # Apply coupon first
    discounted_subtotal = cart.apply_discount(subtotal, 20)
    shipping_on_discounted = cart.shipping_fee(discounted_subtotal, member=True)
    expected_member = round(discounted_subtotal + shipping_on_discounted, 2)
    assert c.total(member=True, coupon="SAVE20") == expected_member

# Test that an invalid coupon raises ValueError.
# ---------------------------------------------------------------------------
def test_cart_total_invalid_coupon():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
