import pytest
import cart

# Tests for apply_discount
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [(-10, 20), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# Tests for bulk_discount_percent
@pytest.mark.parametrize("quantity,percent", [
    (5, 0),
    (10, 5),
    (30, 10),
    (120, 15),
])
def test_bulk_discount_percent(quantity, percent):
    assert cart.bulk_discount_percent(quantity) == percent

@pytest.mark.parametrize("quantity", [0, -1, 2.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# Tests for parse_coupon
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    (" save20 ", 20),
    ("SaVe5", 5),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", [
    "SAV10",
    "SAVE0",
    "SAVE51",
    "ABC123",
    "save-5",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Tests for shipping_fee
@pytest.mark.parametrize("subtotal,member,result", [
    (0, False, 60),
    (999.99, False, 60),
    (1000, False, 0),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, result):
    assert cart.shipping_fee(subtotal, member) == result

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Tests for Cart class behavior
def test_cart_add_and_items():
    c = cart.Cart()
    assert c.items() == {}
    c.add_item("apple", 1.0, 2)
    assert c.items() == {"apple": 2}
    # adding same item with same price increases quantity
    c.add_item("apple", 1.0, 3)
    assert c.items() == {"apple": 5}
    # adding another item
    c.add_item("banana", 0.5)
    assert c.items() == {"apple": 5, "banana": 1}

def test_cart_add_invalid():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("orange", -1.0, 2)
    with pytest.raises(ValueError):
        c.add_item("orange", 1.0, 0)
    with pytest.raises(ValueError):
        c.add_item("orange", 1.0, -3)

    # price mismatch
    c.add_item("pear", 2.0, 1)
    with pytest.raises(ValueError):
        c.add_item("pear", 3.0, 1)

def test_cart_remove_and_total():
    c = cart.Cart()
    c.add_item("widget", 10.0, 5)   # subtotal 50
    c.remove_item("widget", 2)      # remaining 3
    assert c.items() == {"widget": 3}
    # removing more than exists should remove item
    c.remove_item("widget", 5)
    assert c.items() == {}

    with pytest.raises(KeyError):
        c.remove_item("nonexistent", 1)

def test_cart_total_and_subtotal():
    c = cart.Cart()
    c.add_item("book", 30.0, 2)   # subtotal 60
    assert c.subtotal() == 60.0
    # no coupon or membership
    assert c.total() == 90.0  # 60 + shipping 30
    # member gets half shipping
    assert c.total(member=True) == 75.0  # 60 + 15
    # apply coupon SAVE10 -> 10% off subtotal before shipping
    total_with_coupon = 60 * 0.90 + 30
    assert c.total(coupon="SAVE10") == pytest.approx(total_with_coupon)
    # combination: member and coupon
    total_combo = 60 * 0.90 + 15
    assert c.total(member=True, coupon="SAVE10") == pytest.approx(total_combo)

# Test bulk discount applied per item quantity >10

def test_bulk_discount_in_cart_total():
    c = cart.Cart()
    # 12 apples at $5 each -> subtotal 60
    c.add_item("apple", 5.0, 12)   # quantity >=10 => 5% bulk discount
    assert c.subtotal() == 60.0
    # Bulk discount reduces price per unit by 5%
    discounted_price = 5.0 * 0.95
    expected_total_before_shipping = discounted_price * 12
    assert pytest.approx(c.total()) == expected_total_before_shipping + 30

# End of tests
