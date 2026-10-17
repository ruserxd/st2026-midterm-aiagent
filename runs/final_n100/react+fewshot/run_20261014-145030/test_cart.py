import pytest
import cart

# ---------- apply_discount ---------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    # rounding
    assert cart.apply_discount(100, 33) == 67.0
    # percent bounds
    with pytest.raises(ValueError):
        cart.apply_discount(50, -1)
    with pytest.raises(ValueError):
        cart.apply_discount(50, 101)
    # price bounds
    with pytest.raises(ValueError):
        cart.apply_discount(-10, 20)

# ---------- bulk_discount_percent ---------------------------

def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    # invalid quantity
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-3)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0.5)

# ---------- parse_coupon -------------------------------------

def test_parse_coupon():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon(" save20 ") == 20
    # case-insensitive
    assert cart.parse_coupon("SaVe30") == 30
    # bounds
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE0")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE51")
    # invalid format
    with pytest.raises(ValueError):
        cart.parse_coupon("DISCOUNT10")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVEXY")

# ---------- shipping_fee -------------------------------------

def test_shipping_fee():
    assert cart.shipping_fee(999) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0
    # members
    assert cart.shipping_fee(800, member=True) == 30
    assert cart.shipping_fee(1200, member=True) == 0
    with pytest.raises(ValueError):
        cart.shipping_fee(-5)

# ---------- Cart class ----------------------------------------

def test_cart_add_and_items():
    c = cart.Cart()
    assert c.items() == {}
    c.add_item("apple", 1.50, 3)
    assert c.items() == {"apple": 3}
    # adding same item increases quantity
    c.add_item("apple", 1.50, 2)
    assert c.items() == {"apple": 5}
    # adding different item
    c.add_item("banana", 0.75)
    assert c.items() == {"apple": 5, "banana": 1}
    with pytest.raises(ValueError):
        c.add_item("orange", -2.00)
    with pytest.raises(ValueError):
        c.add_item("orange", 1.20, 0)


def test_cart_remove():
    c = cart.Cart()
    c.add_item("apple", 1.00, 5)
    c.remove_item("apple", 2)
    assert c.items() == {"apple": 3}
    # remove enough to delete item
    c.remove_item("apple", 3)
    assert c.items() == {}
    # removing non‑existent raises KeyError
    with pytest.raises(KeyError):
        c.remove_item("banana")


def test_cart_subtotal_and_bulk():
    c = cart.Cart()
    # No items: subtotal 0
    assert c.subtotal() == 0
    # Add item below bulk thresholds
    c.add_item("pen", 2.00, 9)  # quantity 9 -> no discount
    assert c.subtotal() == 18.00
    # Add more to trigger bulk discounts
    c.remove_item("pen", 9)
    c.add_item("pen", 2.00, 10)  # 5% off
    assert c.subtotal() == round(20 * 0.95, 2)
    c.remove_item("pen", 10)
    c.add_item("pen", 2.00, 50)  # 10% off
    assert c.subtotal() == round(100 * 0.90, 2)
    c.remove_item("pen", 50)
    c.add_item("pen", 2.00, 100)  # 15% off
    assert c.subtotal() == round(200 * 0.85, 2)


def test_cart_total_and_coupon_shipping():
    c = cart.Cart()
    # Empty cart: total 0
    assert c.total() == 0
    # Add items
    c.add_item("tshirt", 20.00, 5)   # no bulk discount
    # subtotal: 100
    assert c.subtotal() == 100.00
    # Without coupon or membership
    assert c.total() == round(100 + cart.shipping_fee(100), 2)
    # With member shipping half fee
    assert c.total(member=True) == round(100 + cart.shipping_fee(100, member=True), 2)
    # Apply a valid coupon (e.g., 10%)
    subtotal_after_coupon = round(100 * (1 - cart.parse_coupon("SAVE10") / 100), 2)
    expected_total = round(subtotal_after_coupon + cart.shipping_fee(subtotal_after_coupon, member=False), 2)
    assert c.total(coupon="SAVE10") == expected_total
    # Invalid coupon should raise ValueError
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# ---------- Test interactions of shipping and discounts ------------

def test_shipping_free_for_large_subtotal():
    c = cart.Cart()
    c.add_item("expensive", 200.00, 10)  # subtotal before bulk: 2000
    assert c.subtotal() == round(2000 * (1 - cart.bulk_discount_percent(10)/100), 2)
    # Since subtotal after bulk is >= 1000, shipping should be free
    assert c.total() == c.subtotal()

# ---------- Edge case: price rounding --------------------------------

def test_apply_discount_rounding():
    # 1% of 33.333... => 0.333..., rounded to two decimals -> 0.33
    assert cart.apply_discount(33.3333, 1) == round(33.3333 * 0.99, 2)
