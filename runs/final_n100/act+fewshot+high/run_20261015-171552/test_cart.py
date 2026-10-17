import pytest
import cart

def test_apply_discount_valid():
    assert cart.apply_discount(200, 15) == 170.0
    expected = round(123.456 * (100 - 10) / 100, 2)
    assert cart.apply_discount(123.456, 10) == expected

def test_apply_discount_errors():
    with pytest.raises(ValueError):
        cart.apply_discount(-1, 10)
    with pytest.raises(ValueError):
        cart.apply_discount(10, -5)
    with pytest.raises(ValueError):
        cart.apply_discount(10, 105)

@pytest.mark.parametrize("qty,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),   # boundary per specification
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("invalid", [0, -1, "5"])
def test_bulk_discount_percent_invalid(invalid):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(invalid)

@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),            # case-insensitive per spec
    (" SAVE30 ", 30),          # surrounding whitespace ignored
    ("sAvE5", 5),              # mixed case
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("invalid", [
    "SAV10",
    "SAVE0",
    "SAVE51",
    "",
    "   ",
    None,
])
def test_parse_coupon_invalid(invalid):
    with pytest.raises(ValueError):
        cart.parse_coupon(invalid)

@pytest.mark.parametrize("subtotal,member,expected", [
    (500, False, 60),
    (500, True, 30),
    (999.99, False, 60),
    (1000, False, 0),
    (1500, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

def test_cart_add_item_basic():
    c = cart.Cart()
    c.add_item("apple", 1.00, quantity=2)
    assert c.items() == {"apple": 2}
    c.add_item("apple", 1.00, quantity=3)
    assert c.items() == {"apple": 5}

def test_cart_add_item_price_mismatch():
    c = cart.Cart()
    c.add_item("apple", 1.00, quantity=2)
    with pytest.raises(ValueError):
        c.add_item("apple", 1.50, quantity=1)

@pytest.mark.parametrize("price,quantity", [
    (-1, 1),   # negative price
    (1, 0),    # zero quantity
    (1, -5),   # negative quantity
    (1, "x"),  # non-integer quantity
])
def test_cart_add_item_invalid_params(price, quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("pear", price, quantity=quantity)

def test_cart_remove_partial():
    c = cart.Cart()
    c.add_item("banana", 2.0, quantity=3)
    c.remove_item("banana", quantity=1)
    assert c.items() == {"banana": 2}

def test_cart_remove_to_zero():
    c = cart.Cart()
    c.add_item("pear", 4.0, quantity=1)
    c.remove_item("pear", quantity=1)
    # Item should be removed entirely
    assert "pear" not in c.items()

def test_cart_remove_more_than_present():
    c = cart.Cart()
    c.add_item("orange", 3.0, quantity=2)
    c.remove_item("orange", quantity=5)  # more than present
    assert "orange" not in c.items()

def test_cart_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("pear")

def test_cart_subtotal():
    c = cart.Cart()
    c.add_item("item1", 10.0, quantity=5)   # no discount
    c.add_item("item2", 8.0, quantity=10)  # 5% discount
    c.add_item("item3", 2.0, quantity=50)  # 10% discount
    c.add_item("item4", 3.0, quantity=100) # 15% discount

    expected = round(
        cart.apply_discount(10.0 * 5, 0) +
        cart.apply_discount(8.0 * 10, 5) +
        cart.apply_discount(2.0 * 50, 10) +
        cart.apply_discount(3.0 * 100, 15),
        2
    )
    assert c.subtotal() == expected

def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0

def test_cart_total_no_coupon():
    c = cart.Cart()
    c.add_item("item", 100.0, quantity=5)   # subtotal 500
    expected_shipping = cart.shipping_fee(500, member=False)
    assert c.total() == round(500 + expected_shipping, 2)

def test_cart_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("big", 200.0, quantity=6)   # subtotal 1200
    assert c.total() == 1200

    percent = cart.parse_coupon("SAVE20")
    amount_after_discount = cart.apply_discount(c.subtotal(), percent)
    expected_total_no_member = round(amount_after_discount + cart.shipping_fee(amount_after_discount, member=False), 2)
    assert c.total(coupon="SAVE20") == expected_total_no_member

    expected_total_member = round(amount_after_discount + cart.shipping_fee(amount_after_discount, member=True), 2)
    assert c.total(member=True, coupon="SAVE20") == expected_total_member

def test_cart_total_coupon_crossing_threshold_exact():
    c = cart.Cart()
    c.add_item("big", 200.0, quantity=5)   # subtotal 1000
    assert c.total() == 1000

    percent = cart.parse_coupon("SAVE10")
    amount_after_discount = cart.apply_discount(c.subtotal(), percent)
    expected_total_no_member = round(amount_after_discount + cart.shipping_fee(amount_after_discount, member=False), 2)
    assert c.total(coupon="SAVE10") == expected_total_no_member

def test_cart_total_invalid_coupon():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
