import pytest
import cart

# Helper for expected behavior based on specifications.

def test_apply_discount_valid():
    assert cart.apply_discount(200, 15) == 170.0
    # check rounding and bounds
    assert cart.apply_discount(123.45, 20) == round(123.45 * 0.80, 2)

# Test boundary conditions for apply_discount
@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# Bulk discount percent tests

def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@pytest.mark.parametrize("quantity", [0, -5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# Coupon parsing tests

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save25") == 25
    assert cart.parse_coupon(" Save5 ") == 5

@pytest.mark.parametrize("code", ["savex", "SAVExx", "abc10", "", "SAVE0", "SAVE51"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Shipping fee tests

def test_shipping_fee():
    assert cart.shipping_fee(999) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0
    # members pay half
    assert cart.shipping_fee(999, member=True) == 30
    assert cart.shipping_fee(500, member=True) == 30

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart class tests

def test_cart_items_empty():
    c = cart.Cart()
    assert c.items() == {}


def test_cart_add_and_remove():
    c = cart.Cart()
    c.add_item("apple", 1.00, quantity=2)
    assert c.items() == {"apple": 2}
    # adding same item increases quantity if unit price matches
    c.add_item("apple", 1.00, quantity=3)
    assert c.items() == {"apple": 5}
    # test price mismatch raises ValueError
    with pytest.raises(ValueError):
        c.add_item("apple", 1.50, quantity=1)

    c.remove_item("apple", quantity=2)
    assert c.items() == {"apple": 3}
    # remove more than present: should remove item completely
    c.remove_item("apple", quantity=5)
    assert "apple" not in c.items()
    # removing non-existent item raises KeyError
    with pytest.raises(KeyError):
        c.remove_item("banana")

# Subtotal calculation

def test_cart_subtotal():
    c = cart.Cart()
    c.add_item("banana", 0.50, quantity=3)
    c.add_item("orange", 1.25, quantity=2)
    assert c.subtotal() == (0.50 * 3 + 1.25 * 2)

# Total calculation with member and coupon

def test_cart_total_member_and_coupon():
    c = cart.Cart()
    c.add_item("widget", 200.00, quantity=1)  # subtotal 200
    # apply bulk discount: quantity 1 => 0%
    assert c.total(member=False, coupon=None) == 200.00 + cart.shipping_fee(200)
    # member pays half shipping
    assert c.total(member=True, coupon=None) == 200.00 + cart.shipping_fee(200, member=True)
    # with valid coupon
    total_with_coupon = c.total(member=False, coupon="SAVE10")
    expected_subtotal = 200.0
    discount = cart.apply_discount(expected_subtotal, 10)
    shipping = cart.shipping_fee(discount)
    assert total_with_coupon == round(discount + shipping, 2)

# Edge case: bulk discount with quantity >=10 and coupon

def test_cart_total_bulk_and_coupon():
    c = cart.Cart()
    # add 15 items of cheap item for bulk discount percent
    c.add_item("small", 10.0, quantity=15)  # subtotal 150
    bulk_pct = cart.bulk_discount_percent(15)
    discounted_subtotal = cart.apply_discount(150, bulk_pct)
    shipping = cart.shipping_fee(discounted_subtotal)
    total = c.total(member=False, coupon=None)
    assert total == round(discounted_subtotal + shipping, 2)

# Coupon applied after bulk discount should use correct percent

def test_cart_total_coupon_after_bulk():
    c = cart.Cart()
    c.add_item("medium", 100.0, quantity=20)  # subtotal 2000
    # Bulk discount 15%
    discounted_subtotal = cart.apply_discount(2000, 15)
    shipping = cart.shipping_fee(discounted_subtotal)
    total = c.total(member=False, coupon="SAVE5")
    expected = cart.apply_discount(round(discounted_subtotal + shipping, 2), 5)
    assert total == round(expected, 2)
