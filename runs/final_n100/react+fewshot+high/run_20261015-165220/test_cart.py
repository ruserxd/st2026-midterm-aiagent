import pytest
import cart

# Apply discount tests
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200.0, 15, 170.00),
        (100.0, 0, 100.00),
        (50.0, 100, 0.00),
        (99.999, 10, round(99.999 * 0.9, 2)),
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == pytest.approx(expected, rel=1e-12)

@pytest.mark.parametrize(
    "price,percent",
    [
        (-10.0, 20),
        (100.0, -5),
        (100.0, 101),
    ],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# Bulk discount percent tests
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (5, 0),      # <10
        (9, 0),      # <10
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [
        0,
        -1,
        3.5,
        None,
    ],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# Parse coupon tests
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),          # should be case-insensitive per spec
        ("  SaVe30 ", 30),       # whitespace trimmed, mixed case
        ("SaVe5", 5),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "DISCOUNT10",
        "SAVE0",
        "SAVE51",
        "save-10",
        "12SAVE",
        None,
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Shipping fee tests
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (1200.0, False, 0),
        (1000.0, False, 0),
        (999.99, False, 60),
        (800.0, False, 60),
        (800.0, True, 30),
        (-10.0, False, None),    # Expect ValueError
    ],
)
def test_shipping_fee(subtotal, member, expected):
    if subtotal < 0:
        with pytest.raises(ValueError):
            cart.shipping_fee(subtotal, member)
    else:
        assert cart.shipping_fee(subtotal, member) == expected

# Cart tests
def test_cart_initial_state():
    c = cart.Cart()
    assert isinstance(c.items(), dict)
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

def test_add_item_basic_and_duplicate_price():
    c = cart.Cart()
    c.add_item("apple", 1.50, 2)
    assert c.items() == {"apple": 2}
    # Add same item with same unit price
    c.add_item("apple", 1.50, 3)
    assert c.items() == {"apple": 5}

@pytest.mark.parametrize(
    "name,price,quantity",
    [
        ("bad", -1.0, 1),
        ("bad", 1.0, 0),   # zero quantity not allowed
        ("bad", 1.0, -2),
    ],
)
def test_add_item_invalid(name, price, quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item(name, price, quantity)

def test_add_item_duplicate_price_mismatch():
    c = cart.Cart()
    c.add_item("item", 10.0, 1)
    with pytest.raises(ValueError):
        c.add_item("item", 12.0, 1)

def test_remove_item_and_deletion():
    c = cart.Cart()
    c.add_item("apple", 1.0, 5)
    # Remove fewer than quantity
    c.remove_item("apple", 3)
    assert c.items() == {"apple": 2}
    # Remove more than remaining quantity: should delete the item
    c.remove_item("apple", 5)
    assert c.items() == {}

def test_remove_exact_quantity_deletes_item():
    c = cart.Cart()
    c.add_item("item", 10.0, 5)
    c.remove_item("item", 5)   # Should remove item completely per spec
    assert c.items() == {}
    # Subtotal should be zero
    assert c.subtotal() == 0

def test_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("banana", 1)

def test_items_returns_copy():
    c = cart.Cart()
    c.add_item("apple", 1, 2)
    items_dict = c.items()
    items_dict["apple"] = 99
    # Original should remain unchanged
    assert c.items() == {"apple": 2}

def test_subtotal_bulk_discount_and_rounding():
    c = cart.Cart()
    c.add_item("apple", 1.23, 5)   # no discount
    c.add_item("banana", 2.0, 12)  # quantity>=10 => 5% discount
    expected = round(1.23 * 5 + cart.apply_discount(2.0 * 12, 5), 2)
    assert c.subtotal() == pytest.approx(expected, rel=1e-12)

def test_subtotal_rounding_edge_case():
    # Test a case where rounding is needed
    c = cart.Cart()
    # quantity 51 => bulk discount percent 10%
    c.add_item("pear", 1.01, 51)
    line_total = 1.01 * 51
    discounted = round(line_total * (100 - 10) / 100, 2)
    assert c.subtotal() == pytest.approx(discounted, rel=1e-12)

@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (900.0, False, 960.0),
        (900.0, True, 930.0),
        (1200.0, False, 1260.0),   # shipping free
        (1200.0, True, 1260.0),
    ],
)
def test_total_no_coupon(subtotal, member, expected):
    c = cart.Cart()
    c.add_item("dummy", subtotal, 1)  # quantity=1 ensures no bulk discount
    assert c.subtotal() == pytest.approx(subtotal, rel=1e-12)
    assert c.total(member=member) == pytest.approx(expected, rel=1e-12)

def test_total_with_coupon_below_threshold():
    c = cart.Cart()
    # subtotal 800
    c.add_item("dummy", 800.0, 1)
    # Coupon percent is 20%
    discounted_amount = round(800.0 * (100 - 20) / 100, 2)
    shipping_fee_non_member = 60 if discounted_amount < 1000 else 0
    expected_total_non_member = round(discounted_amount + shipping_fee_non_member, 2)

    shipping_fee_member = (shipping_fee_non_member / 2) if shipping_fee_non_member else 0
    expected_total_member = round(discounted_amount + shipping_fee_member, 2)

    assert c.total(coupon="SAVE20") == pytest.approx(expected_total_non_member, rel=1e-12)
    assert c.total(member=True, coupon="SAVE20") == pytest.approx(expected_total_member, rel=1e-12)

def test_total_with_coupon_above_threshold_bug():
    # This test expects shipping fee based on discounted subtotal per spec,
    # but the implementation mistakenly uses original subtotal for shipping.
    c = cart.Cart()
    # Original subtotal 1200
    c.add_item("dummy", 1200.0, 1)
    discounted_amount = round(1200.0 * (100 - 20) / 100, 2)   # 960
    shipping_fee_non_member = 60 if discounted_amount < 1000 else 0
    expected_total_spec = round(discounted_amount + shipping_fee_non_member, 2)
    actual_total = c.total(coupon="SAVE20")
    assert actual_total == pytest.approx(expected_total_spec, rel=1e-12), \
        f"Expected total {expected_total_spec} per spec, but got {actual_total}"

def test_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("dummy", 100.0, 1)
    with pytest.raises(ValueError):
        c.total(coupon="DISCOUNT10")

def test_empty_cart_total_any_member_or_coupon_returns_zero():
    c = cart.Cart()
    assert c.total() == 0
    assert c.total(member=True) == 0
    assert c.total(coupon="SAVE10") == 0
