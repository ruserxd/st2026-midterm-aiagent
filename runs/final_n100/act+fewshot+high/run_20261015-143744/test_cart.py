import pytest
import cart

# Helper function for expected apply_discount calculation based on specification
def calc_apply_discount(price, percent):
    return round(price * (100 - percent) / 100, 2)

# Tests for apply_discount
@pytest.mark.parametrize("price,percent,expected", [
    (200.0, 15, 170.0),
    (100.0, 0, 100.0),
    (100.0, 100, 0.0),
    (5.0, 33, 3.35),
    (99.99, 33, 66.99),
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price,percent", [
    (-1.0, 10),
    (100.0, -5),
    (100.0, 105),
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# Tests for bulk_discount_percent
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 0.5, "10"])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# Tests for parse_coupon
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save25", 25),
    ("  SaVe50  ", 50),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVE0",
    "SAVE51",
    "SAVEXX",
    "XX10",
    "",
    "   ",
    123,
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Tests for shipping_fee
@pytest.mark.parametrize("subtotal,member,expected", [
    (999.0, False, 60),
    (1000.0, False, 0),
    (1500.0, False, 0),
    (500.0, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Tests for Cart class
def test_cart_initial_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0

@pytest.mark.parametrize("name,unit_price,quantity", [
    ("apple", -1.0, 2),
    ("orange", 5.0, 0),
    ("pear", 3.0, 2.5),
])
def test_cart_add_item_invalid(name, unit_price, quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item(name, unit_price, quantity)

def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item("apple", 1.5, 2)
    assert c.items() == {"apple": 2}
    c.add_item("apple", 1.5, 3)
    assert c.items() == {"apple": 5}
    with pytest.raises(ValueError):
        c.add_item("apple", 2.0, 1)

def test_cart_remove_item():
    c = cart.Cart()
    c.add_item("banana", 0.75, 5)
    # Partial removal
    c.remove_item("banana", 3)
    assert c.items() == {"banana": 2}
    # Remove one more
    c.remove_item("banana")  # default quantity=1
    assert c.items() == {"banana": 1}
    # Remove exactly the remaining quantity -> item should be removed
    c.remove_item("banana", 1)
    assert "banana" not in c.items()
    # Removing more than remaining also removes the item
    c.add_item("grape", 2.0, 4)
    c.remove_item("grape", 10)
    assert "grape" not in c.items()
    with pytest.raises(KeyError):
        c.remove_item("orange")

def test_cart_items_copy():
    c = cart.Cart()
    c.add_item("grape", 2.0, 4)
    d = c.items()
    d["grape"] = 100
    assert c.items()["grape"] == 4

def test_cart_subtotal_simple():
    c = cart.Cart()
    c.add_item("book", 20.0, 12)   # bulk discount 5%
    c.add_item("pen", 10.0, 3)
    expected = cart.apply_discount(240.0, 5) + 30.0
    assert c.subtotal() == pytest.approx(expected)

def test_cart_subtotal_rounding():
    c = cart.Cart()
    c.add_item("widget", 19.99, 11)   # bulk discount 5%
    c.add_item("pen", 10.0, 3)
    widget_total = cart.apply_discount(19.99 * 11, 5)
    pen_total = 30.0
    expected_subtotal = round(widget_total + pen_total, 2)
    assert c.subtotal() == pytest.approx(expected_subtotal)

def test_cart_total_no_coupon_shipping():
    c = cart.Cart()
    c.add_item("item", 900.0, 1)
    expected_total = 960.0
    assert c.total() == pytest.approx(expected_total)

def test_cart_total_free_shipping():
    c = cart.Cart()
    c.add_item("item", 1000.0, 1)
    assert c.total() == pytest.approx(1000.0)

def test_cart_total_coupon_affect_shipping():
    c = cart.Cart()
    c.add_item("item", 1100.0, 1)
    expected_total = 940.0
    assert c.total(coupon="SAVE20") == pytest.approx(expected_total)

def test_cart_total_coupon_member_shipping():
    c = cart.Cart()
    c.add_item("item", 1050.0, 1)
    expected_total = 1027.5
    assert c.total(member=True, coupon="SAVE5") == pytest.approx(expected_total)

def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("item", 500.0, 1)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")

def test_cart_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0.0

def test_cart_total_rounding_final():
    c = cart.Cart()
    c.add_item("item", 199.99, 1)
    discounted_subtotal = cart.apply_discount(199.99, 10)   # 179.99
    shipping_fee_val = cart.shipping_fee(discounted_subtotal, False)
    expected_total = round(discounted_subtotal + shipping_fee_val, 2)
    assert c.total(coupon="SAVE10") == pytest.approx(expected_total)

def test_cart_total_rounding_member():
    c = cart.Cart()
    c.add_item("item", 199.99, 1)
    discounted_subtotal = cart.apply_discount(199.99, 10)   # 179.99
    shipping_fee_val = cart.shipping_fee(discounted_subtotal, True)
    expected_total = round(discounted_subtotal + shipping_fee_val, 2)
    assert c.total(member=True, coupon="SAVE10") == pytest.approx(expected_total)
