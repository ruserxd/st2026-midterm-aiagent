import pytest
import cart

# Helper to create a simple cart

def make_simple_cart():
    c = cart.Cart()
    c.add_item("apple", unit_price=1.5, quantity=2)
    c.add_item("banana", unit_price=0.75, quantity=4)
    return c

# Test adding items and quantity aggregation

def test_add_and_items():
    c = cart.Cart()
    c.add_item("itemA", 10, 1)
    assert c.items() == {"itemA": 1}
    # add same item increases quantity
    c.add_item("itemA", 10, 3)
    assert c.items() == {"itemA": 4}
    # adding with different unit price raises ValueError
    with pytest.raises(ValueError):
        c.add_item("itemA", 12, 1)
    # negative price or quantity raises ValueError
    with pytest.raises(ValueError):
        c.add_item("badPrice", -5, 1)
    with pytest.raises(ValueError):
        c.add_item("badQty", 5, 0)

# Test removing items

def test_remove_and_zero_removal():
    c = cart.Cart()
    c.add_item("itemB", 3, 2)
    c.remove_item("itemB", 1)
    assert c.items() == {"itemB": 1}
    # remove remaining
    c.remove_item("itemB", 1)
    assert "itemB" not in c.items()
    # removing nonexistent raises KeyError
    with pytest.raises(KeyError):
        c.remove_item("noItem", 1)

# Test subtotal calculation

def test_subtotal():
    c = make_simple_cart()
    # apple: 2 * 1.5 = 3, banana: 4 * 0.75 = 3, total = 6
    assert c.subtotal() == pytest.approx(6)

# Test total with coupon and member discount

def test_total_with_coupon_and_member():
    c = make_simple_cart()
    # subtotal 6, no coupon, non-member shipping: assume shipping_fee returns 2.0 for simplicity? We'll compute using cart.shipping_fee directly
    base = c.subtotal()
    shipping = cart.shipping_fee(base)
    expected_total = round(base + shipping, 2)
    assert c.total() == pytest.approx(expected_total)

    # Now test with a valid coupon code that gives 20% off
    # parse_coupon('DISCOUNT-20') should return 20
    percent = cart.parse_coupon("DISCOUNT-20")
    assert percent == 20
    discounted_subtotal = base * (1 - percent / 100)
    shipping_with_coupon = cart.shipping_fee(discounted_subtotal)
    expected_total_coupon = round(discounted_subtotal + shipping_with_coupon, 2)
    assert c.total(coupon="DISCOUNT-20") == pytest.approx(expected_total_coupon)

# Test invalid coupon raises ValueError

def test_invalid_coupon():
    with pytest.raises(ValueError):
        cart.parse_coupon("BADCODE")

# Test empty cart total is zero (no shipping)

def test_empty_cart_total_zero():
    c = cart.Cart()
    assert c.total() == 0
