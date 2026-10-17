import pytest
import cart

# Helper function to create a cart with some items

def make_sample_cart():
    c = cart.Cart()
    # Add two items: apples at $1 each, bananas at $2 each
    c.add_item("apple", 1.00, quantity=3)   # 3 apples => $3.00
    c.add_item("banana", 2.00, quantity=2)  # 2 bananas => $4.00
    return c

# Specification-derived expected values:
# - apple: unit_price 1.00, qty 3, total 3.00
# - banana: unit_price 2.00, qty 2, total 4.00
# Subtotal = 7.00
# No discounts unless specified.
# Shipping fee for non-members with subtotal <=50: $10.0; members: free.
# Bulk discount: 5% if quantity >=10.
# apply_discount should reduce price by percent/100.
# parse_coupon returns coupon dict.

# Tests for helper functions

def test_apply_discount():
    assert cart.apply_discount(100, 20) == pytest.approx(80.0)
    # discount of 0% -> same price
    assert cart.apply_discount(50, 0) == 50
    # percent > 100 should give negative price? spec not defined; test normal case


def test_bulk_discount_percent():
    # quantity less than threshold returns 0%
    assert cart.bulk_discount_percent(9) == 0
    # exact threshold gives 5%
    assert cart.bulk_discount_percent(10) == 5
    # above threshold still 5%
    assert cart.bulk_discount_percent(15) == 5


def test_parse_coupon():
    code = "SAVE20"
    coupon = cart.parse_coupon(code)
    assert isinstance(coupon, dict)
    assert coupon["code"] == code
    # Discount percent should be a float between 0 and 100.
    assert 0 <= coupon["discount_percent"] <= 100


def test_shipping_fee():
    # subtotal less than or equal to 50
    assert cart.shipping_fee(45) == 10.0
    assert cart.shipping_fee(50, member=True) == 0.0
    # above threshold free for all
    assert cart.shipping_fee(75) == 0.0

# Tests for Cart class behavior

def test_cart_initially_empty():
    c = cart.Cart()
    assert c.items() == []
    assert c.subtotal() == 0
    # total with default arguments should equal subtotal + shipping (free if member? assume non-member)
    assert c.total(member=False) == pytest.approx(10.0)


def test_add_and_remove_items():
    c = cart.Cart()
    c.add_item("apple", 1.50, quantity=2)
    items = c.items()
    assert len(items) == 1
    assert items[0]["name"] == "apple"
    assert items[0]["unit_price"] == 1.5
    assert items[0]["quantity"] == 2
    # subtotal should be 3.00
    assert c.subtotal() == pytest.approx(3.0)

    # Remove one apple
    c.remove_item("apple", quantity=1)
    assert c.items()[0]["quantity"] == 1
    assert c.subtotal() == pytest.approx(1.5)

    # Removing more than exists should remove item entirely (spec unclear; test removal to zero)
    c.remove_item("apple", quantity=5)
    assert c.items() == []
    assert c.subtotal() == 0


def test_bulk_discount_applied_in_total():
    c = cart.Cart()
    # Add 10 units of a product with price $10 each -> subtotal $100, bulk discount 5% => $95.00
    c.add_item("widget", 10.00, quantity=10)
    assert c.subtotal() == pytest.approx(100.0)
    # Total should apply bulk discount and no shipping (subtotal >50) so total = 95
    assert c.total(member=False) == pytest.approx(95.0)


def test_coupon_discount_in_total():
    c = cart.Cart()
    c.add_item("widget", 20.00, quantity=1)
    coupon_code = "SAVE10"
    # Parse coupon to get discount percent
    coupon = cart.parse_coupon(coupon_code)
    assert coupon["discount_percent"] == 10.0 or isinstance(coupon["discount_percent"], float)
    # Total with coupon should apply 10% discount on subtotal ($20) => $18 + shipping (free? subtotal <=50, non-member so $10) => $28
    total_with_coupon = c.total(member=False, coupon=coupon_code)
    assert total_with_coupon == pytest.approx(28.0)


def test_bulk_and_coupon_combined():
    c = cart.Cart()
    # 15 widgets at $10 each -> subtotal $150, bulk discount 5% => $142.50
    c.add_item("widget", 10.00, quantity=15)
    coupon_code = "SAVE20"
    total_with_coupon = c.total(member=False, coupon=coupon_code)
    # Coupon applied after bulk discount: 20% off $142.5 = $114.0
    assert total_with_coupon == pytest.approx(114.0)

# Edge case tests for subtotal and shipping

def test_subtotal_and_shipping_edge_cases():
    c = cart.Cart()
    # Subtotal exactly $50 should still incur shipping of $10 if non-member
    c.add_item("item", 25.00, quantity=2)
    assert c.subtotal() == pytest.approx(50.0)
    assert c.total(member=False) == pytest.approx(60.0)
    # Member with subtotal exactly $50 should have free shipping
    assert c.total(member=True) == pytest.approx(50.0)

# Ensure that add_item does not allow negative price or quantity

def test_add_invalid_inputs():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("bad", -5.00, quantity=1)
    with pytest.raises(ValueError):
        c.add_item("bad", 5.00, quantity=-3)

# Ensure remove_item raises when item not present or quantity zero

def test_remove_invalid():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent")
    c.add_item("foo", 1.00, quantity=1)
    with pytest.raises(ValueError):
        c.remove_item("foo", quantity=0)
