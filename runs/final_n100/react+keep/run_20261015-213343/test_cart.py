import pytest
import cart

def round2(x):
    return round(float(x), 2)

# ---------- Tests for standalone functions ----------

def test_apply_discount_valid():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(100, 100) == 0.0

@ pytest.mark.parametrize("price", [-10, -1e-9])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [ -5, 105, 101 ])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(50, percent)

# bulk discount thresholds and error handling

def test_bulk_discount_percent_thresholds():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(25) == 5  # expected from spec (not 10)
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(70) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

def test_bulk_discount_percent_invalid():
    for qty in [0, -1, -10]:
        with pytest.raises(ValueError):
            cart.bulk_discount_percent(qty)

# coupon parsing

def test_parse_coupon_valid_cases():
    assert cart.parse_coupon("SAVE10") == 10
    # whitespace should be ignored per spec
    assert cart.parse_coupon("save50 ") == 50
    assert cart.parse_coupon(" SAVE5") == 5

@ pytest.mark.parametrize("code", ["", "SAV", "SAVE0", "SAVE51", "DISCOUNT10", "savelow"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping fee logic

def test_shipping_fee_non_member():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(500) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(2000) == 0

def test_shipping_fee_member():
    assert cart.shipping_fee(10, member=True) == 30
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(1000, member=True) == 0

@ pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Tests for Cart class behavior ----------

def test_cart_initial_state():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    total = c.total()
    assert isinstance(total, (int, float)) and total >= 0

def test_add_and_remove_items():
    c = cart.Cart()
    c.add_item("apple", unit_price=50, quantity=2)
    assert c.items()["apple"] == (50, 2)
    c.add_item("apple", unit_price=50, quantity=3)
    assert c.items()["apple"] == (50, 5)
    c.remove_item("apple", quantity=2)
    assert c.items()["apple"] == (50, 3)
    c.remove_item("apple", quantity=5)
    assert "apple" not in c.items()

def test_subtotal_and_total():
    c = cart.Cart()
    c.add_item("banana", 100, 3)   # subtotal 300
    c.add_item("orange", 150, 2)   # subtotal 600
    assert c.subtotal() == 600
    expected_total_without_discounts = 600 + cart.shipping_fee(600)
    assert c.total() == expected_total_without_discounts

    c_member_coupon = cart.Cart()
    c_member_coupon.add_item("item", 200, 1)   # subtotal 200
    total_with_member = c_member_coupon.total(member=True)
    assert total_with_member == 200 + 30

    total_with_coupon = c_member_coupon.total(coupon="SAVE10")
    discounted_subtotal = cart.apply_discount(200, 10)
    expected_total_coupon = discounted_subtotal + cart.shipping_fee(discounted_subtotal)
    assert total_with_coupon == round2(expected_total_coupon)

    total_full_combo = c_member_coupon.total(member=True, coupon="SAVE10")
    expected_full_combo = discounted_subtotal + 30
    assert total_full_combo == round2(expected_full_combo)

# Edge case: attempting to remove non-existent item should not raise error

def test_remove_nonexistent_item():
    c = cart.Cart()
    try:
        c.remove_item("nonexistent", quantity=1)
    except Exception as e:
        pytest.fail(f"remove_item raised an exception for nonexistent item: {e}")

# Test that subtotal updates correctly after multiple operations

def test_subtotal_updates():
    c = cart.Cart()
    c.add_item("widget", 75, 4)   # subtotal 300
    assert c.subtotal() == 300
    c.remove_item("widget", 1)
    assert c.subtotal() == 225
    c.add_item("widget", 75, 2)
    assert c.subtotal() == 375
