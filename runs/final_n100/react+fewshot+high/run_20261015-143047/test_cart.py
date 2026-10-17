import pytest
import cart

# Test coupon parsing

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 0.10
    assert cart.parse_coupon("HALFOFF") == 0.50


def test_parse_coupon_invalid():
    with pytest.raises(ValueError):
        cart.parse_coupon("INVALIDCODE")

# Test Cart initialization and empty total

def test_cart_init_and_total_empty():
    c = cart.Cart()
    assert c.total() == 0.00

# Test adding items and computing total

def test_add_and_total():
    c = cart.Cart()
    c.add("item1", 10.00)
    assert c.total() == 10.00
    c.add("item2", 5.50)
    assert c.total() == 15.50

# Test removing items and error on missing item

def test_remove():
    c = cart.Cart()
    c.add("item1", 3.00)
    c.remove("item1")
    assert c.total() == 0.00
    with pytest.raises(ValueError):
        c.remove("nonexistent_item")

# Test applying valid coupon and total after discount

def test_apply_coupon_and_total():
    c = cart.Cart()
    c.add("item1", 20.00)
    c.apply_coupon("SAVE10")
    assert c.total() == round(20 * (1 - 0.10), 2)

# Test applying invalid coupon raises ValueError

def test_apply_invalid_coupon():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.apply_coupon("BADCODE")
