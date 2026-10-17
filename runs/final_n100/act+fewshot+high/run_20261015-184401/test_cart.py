import pytest
import cart

# --------- apply_discount ----------
def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0

@pytest.mark.parametrize("price,percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

def test_apply_discount_rounding():
    # 199.99 * 0.9 = 179.991 -> round to 179.99
    assert cart.apply_discount(199.99, 10) == round(199.99 * 0.9, 2)

# --------- bulk_discount_percent ----------
@pytest.mark.parametrize("quantity,expected", [
    (9, 0), (10, 5), (49, 5),
    (50, 10), (99, 10), (100, 15), (150, 15)
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, "ten"])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --------- parse_coupon ----------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10), ("save20", 20),
    (" SAVE30 ", 30), ("Save1", 1), ("savE50", 50)
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "DISCOUNT10", "SAVE0", "SAVE51",
    "SAVE5A", "SAVEX", "", "   ", 123
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --------- shipping_fee ----------
@pytest.mark.parametrize("subtotal,member,expected", [
    (1200, False, 0), (1000, False, 0),
    (999.99, False, 60), (999.99, True, 30)
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

def test_shipping_fee_negative_subtotal():
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

# --------- Cart ----------
def test_cart_empty_initial_state():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

def test_cart_add_item_basic():
    c = cart.Cart()
    c.add_item("apple", 1.00, 3)
    assert c.items() == {"apple": 3}
    # No bulk discount for quantity 3
    assert c.subtotal() == 3.0

def test_cart_add_same_unit_price_increments():
    c = cart.Cart()
    c.add_item("banana", 2.5, 4)
    c.add_item("banana", 2.5, 6)
    # Total quantity should be 10
    assert c.items() == {"banana": 10}
    # Bulk discount for 10 units: 5%
    expected_subtotal = round(2.5 * 10 * (100 - 5) / 100, 2)
    assert c.subtotal() == expected_subtotal

def test_cart_add_item_mismatched_price_error():
    c = cart.Cart()
    c.add_item("pear", 1.0)
    with pytest.raises(ValueError):
        c.add_item("pear", 2.0, 1)

@pytest.mark.parametrize("qty", [0, -5])
def test_cart_add_item_invalid_quantity(qty):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("orange", 1.0, qty)

def test_cart_remove_item_decrement():
    c = cart.Cart()
    c.add_item("apple", 1.0, 5)
    c.remove_item("apple", 2)
    assert c.items() == {"apple": 3}

def test_cart_remove_item_to_zero_bug():
    c = cart.Cart()
    c.add_item("pear", 1.0, 4)
    # Remove all
    c.remove_item("pear", 4)
    # According to spec, item should be removed
    assert "pear" not in c.items()

def test_cart_remove_item_more_than_quantity():
    c = cart.Cart()
    c.add_item("melon", 2.0, 3)
    c.remove_item("melon", 5)  # should remove the item entirely
    assert "melon" not in c.items()

def test_cart_remove_nonexistent_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent")

def test_cart_subtotal_rounding():
    c = cart.Cart()
    # 0.99 * 10 = 9.90 -> bulk discount 5% => 9.405 -> round to 9.41
    c.add_item("candy", 0.99, 10)
    expected = round(9.9 * (100 - 5) / 100, 2)  # 9.41
    assert c.subtotal() == expected

def test_cart_total_no_coupon():
    c = cart.Cart()
    c.add_item("item", 50, 5)  # subtotal = 250
    expected = round(250 + cart.shipping_fee(250), 2)
    assert c.total() == expected

def test_cart_total_with_member_shipping():
    c = cart.Cart()
    c.add_item("item", 200, 6)  # subtotal 1200 > free shipping
    expected_total = round(1200 + cart.shipping_fee(1200, member=True), 2)
    assert c.total(member=True) == expected_total

def test_cart_total_with_coupon_shipping_mismatch():
    """
    This test reveals that the implementation uses the original subtotal for
    calculating shipping instead of the discounted amount, which is a bug.
    According to the specification, shipping should be calculated on the
    amount after applying the coupon discount.
    """
    c = cart.Cart()
    # Build a cart with subtotal > 1000 but after coupon < 1000
    c.add_item("expensive", 200, 6)          # original subtotal: 1200
    assert c.subtotal() == 1200              # confirm subtotal

    # Apply a 20% discount via coupon "SAVE20"
    amount_after_coupon = cart.apply_discount(c.subtotal(), cart.parse_coupon("SAVE20"))
    shipping_fee_on_discounted_amount = cart.shipping_fee(amount_after_coupon)
    expected_total = round(amount_after_coupon + shipping_fee_on_discounted_amount, 2)

    # The implementation will return a different total because it calculates
    # shipping on the original subtotal.
    actual_total = c.total(coupon="SAVE20")
    assert actual_total == expected_total

def test_cart_total_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item("item", 10, 1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

def test_cart_total_empty_with_coupon_returns_zero():
    c = cart.Cart()
    assert c.total(coupon="SAVE10") == 0
