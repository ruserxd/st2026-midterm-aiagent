import pytest
import cart

# apply_discount tests
test_apply_discount_cases = [
    (200, 15, 170.0),
    (199, 10, 179.1),           # 199 * 0.9 = 179.1
    (99.99, 33, 66.99),         # rounded to two decimals
    (10, 0, 10.0),
    (100, 100, 0.0)
]

@pytest.mark.parametrize("price, percent, expected", test_apply_discount_cases)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == pytest.approx(expected)

@pytest.mark.parametrize("price, percent", [(-5, 20), (100, -1), (100, 101)])
def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize("quantity, expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15)
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [-1, 0])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize("code, expected", [
    ("SAVE10", 10),
    ("save25", 25),
    (" SAVE50 ", 50),
    ("SaVe1", 1)
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "SAVEX", "", "   ", "NOPE"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal, member, expected", [
    (1000, False, 0),
    (1500, True, 0),
    (999.99, False, 60),
    (500, False, 60),
    (999.99, True, 30),
    (500, True, 30)
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

def test_shipping_fee_negative_subtotal():
    with pytest.raises(ValueError):
        cart.shipping_fee(-1)

# Cart tests
@pytest.mark.parametrize("unit_price, qty", [(-10, 1), (5, -2), (5, 0)])
def test_cart_add_invalid(unit_price, qty):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("Invalid", unit_price, qty)

def test_cart_initial_empty_and_total_zero():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

def test_cart_add_new_item_and_subtotal():
    c = cart.Cart()
    c.add_item("Apple", 100, 3)
    assert c.items() == {"Apple": 3}
    assert c.subtotal() == 300

def test_cart_add_existing_same_price_increases_quantity():
    c = cart.Cart()
    c.add_item("Banana", 50, 2)
    c.add_item("Banana", 50, 1)
    assert c.items() == {"Banana": 3}
    assert c.subtotal() == 150

def test_cart_add_existing_diff_price_raises():
    c = cart.Cart()
    c.add_item("Cherry", 20, 1)
    with pytest.raises(ValueError):
        c.add_item("Cherry", 25, 1)

def test_cart_remove_partial_and_full_removal():
    c = cart.Cart()
    c.add_item("Orange", 30, 3)
    c.remove_item("Orange", 1)   # remaining 2
    assert c.items() == {"Orange": 2}
    assert c.subtotal() == 60
    c.remove_item("Orange", 2)   # should remove item completely
    assert c.items() == {}
    assert c.subtotal() == 0

def test_cart_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("NonExistent", 1)

def test_cart_items_copy_immutable():
    c = cart.Cart()
    c.add_item("Mango", 70, 2)
    items_dict = c.items()
    items_dict["Mango"] = 99   # modify local dict
    assert c.items() == {"Mango": 2}  # original unchanged

def test_cart_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("Widget", 300, 1)          # subtotal 300
    c.add_item("Gadget", 200, 2)          # subtotal 700
    # Without member:
    expected_no_member = round((700 * (1 - 0.10)) + 60, 2)
    assert c.total(member=False, coupon="SAVE10") == pytest.approx(expected_no_member)

    # With member:
    expected_member = round((700 * (1 - 0.10)) + 30, 2)
    assert c.total(member=True, coupon="SAVE10") == pytest.approx(expected_member)

    # Coupon invalid
    with pytest.raises(ValueError):
        c.total(coupon="NOPE")

def test_cart_total_empty_no_shipping():
    c = cart.Cart()
    assert c.total() == 0
    assert c.total(member=True) == 0
    assert c.total(coupon="SAVE10") == 0   # still zero

def test_cart_total_shipping_after_discount():
    c = cart.Cart()
    c.add_item("Expensive", 400, 3)   # subtotal 1200
    expected = round((1200 * (1 - 0.50)) + 60, 2)
    assert c.total(coupon="SAVE50") == pytest.approx(expected)

def test_cart_total_shipping_free_after_discount():
    c = cart.Cart()
    c.add_item("Expensive", 400, 5)   # subtotal 2000
    expected = round((2000 * (1 - 0.50)) + 0, 2)
    assert c.total(coupon="SAVE50") == pytest.approx(expected)
