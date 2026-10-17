import pytest
import cart

# Helper function for bulk discount percent according to spec
def _bulk_discount_percent_expected(quantity):
    if quantity >= 100:
        return 15
    elif quantity >= 50:
        return 10
    elif quantity >= 10:
        return 5
    else:
        return 0

# apply_discount tests
@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),
    (50, 0, 50.0),
    (0, 100, 0.0),
    (99.99, 33, 66.99),  # rounding case
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price,percent", [
    (-10, 50),
    (50, -1),
    (50, 101),
])
def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize("qty,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -1, 2.5, "10"])
def test_bulk_discount_percent_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# parse_coupon tests
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save25", 25),
    ("   SaVe50   ", 50),
    ("sAvE20", 20),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "NOTA", "", "SAVExx"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal,member,expected_fee", [
    (1000, False, 0),
    (999.99, False, 60),
    (999.99, True, 30),
    (500, False, 60),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, expected_fee):
    assert cart.shipping_fee(subtotal, member) == expected_fee

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart tests
def test_cart_initial_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 0.0

def test_cart_add_item_new():
    c = cart.Cart()
    c.add_item("apple", 10, 5)
    assert c.items() == {"apple": 5}
    # No bulk discount
    assert c.subtotal() == 50.0

def test_cart_add_existing_same_price():
    c = cart.Cart()
    c.add_item("apple", 10, 3)
    c.add_item("apple", 10, 2)
    assert c.items() == {"apple": 5}
    assert c.subtotal() == 50.0

def test_cart_add_existing_different_price():
    c = cart.Cart()
    c.add_item("banana", 5, 1)
    with pytest.raises(ValueError):
        c.add_item("banana", 6, 1)

@pytest.mark.parametrize("price", [-1, -0.01])
def test_cart_add_negative_price(price):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("bad", price, 5)

@pytest.mark.parametrize("qty", [0, -1])
def test_cart_add_non_positive_quantity(qty):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("bad", 10, qty)

@pytest.mark.parametrize("qty", [2.5, "5"])
def test_cart_add_invalid_quantity_type(qty):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("bad", 10, qty)

def test_cart_remove_partial():
    c = cart.Cart()
    c.add_item("banana", 20, 12)
    c.remove_item("banana", 5)
    assert c.items() == {"banana": 7}
    assert c.subtotal() == 140.0

def test_cart_remove_overremove_and_clear():
    c = cart.Cart()
    c.add_item("banana", 20, 5)
    c.remove_item("banana", 10)  # removes item entirely
    assert c.items() == {}
    assert c.subtotal() == 0.0

def test_cart_remove_nonexistent_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("cherry")

def test_cart_items_returns_copy():
    c = cart.Cart()
    c.add_item("item1", 5, 3)
    items_dict = c.items()
    items_dict["item1"] = 10
    # Original cart should remain unchanged
    assert c.items()["item1"] == 3

def test_cart_subtotal_basic():
    c = cart.Cart()
    c.add_item("A", 33.3333, 10)
    c.add_item("B", 50, 12)
    # Compute expected subtotal using spec logic
    discounted_A = 33.3333 * 10 * (1 - _bulk_discount_percent_expected(10) / 100)
    discounted_B = 50 * 12 * (1 - _bulk_discount_percent_expected(12) / 100)
    expected_subtotal = round(discounted_A + discounted_B, 2)
    assert c.subtotal() == expected_subtotal

def test_cart_subtotal_with_bulk_discounts_and_rounding():
    c = cart.Cart()
    c.add_item("big", 2, 150)   # 15% discount
    c.add_item("small", 3.75, 9)  # no discount
    c.add_item("medium", 5, 50)   # 10% discount
    discounted_big = 2 * 150 * (1 - _bulk_discount_percent_expected(150) / 100)
    discounted_small = 3.75 * 9 * (1 - _bulk_discount_percent_expected(9) / 100)
    discounted_medium = 5 * 50 * (1 - _bulk_discount_percent_expected(50) / 100)
    expected_subtotal = round(discounted_big + discounted_small + discounted_medium, 2)
    assert c.subtotal() == expected_subtotal

def test_cart_total_no_coupon_no_member():
    c = cart.Cart()
    c.add_item("A", 33.3333, 10)
    c.add_item("B", 50, 12)
    subtotal = c.subtotal()
    shipping_fee = cart.shipping_fee(subtotal)  # default member=False
    expected_total = round(subtotal + shipping_fee, 2)
    assert c.total() == expected_total

def test_cart_total_with_coupon():
    c = cart.Cart()
    c.add_item("A", 33.3333, 10)
    c.add_item("B", 50, 12)
    subtotal = c.subtotal()
    coupon_percent = cart.parse_coupon("SAVE10")
    discounted_amount = subtotal * (1 - coupon_percent / 100)
    shipping_fee = cart.shipping_fee(discounted_amount)  # member=False
    expected_total = round(discounted_amount + shipping_fee, 2)
    assert c.total(coupon="SAVE10") == expected_total

def test_cart_total_with_coupon_and_member():
    c = cart.Cart()
    c.add_item("A", 33.3333, 10)
    c.add_item("B", 50, 12)
    subtotal = c.subtotal()
    coupon_percent = cart.parse_coupon("SAVE10")
    discounted_amount = subtotal * (1 - coupon_percent / 100)
    shipping_fee = cart.shipping_fee(discounted_amount, member=True)
    expected_total = round(discounted_amount + shipping_fee, 2)
    assert c.total(coupon="SAVE10", member=True) == expected_total

def test_cart_total_free_shipping_after_coupon():
    # Cart with subtotal >1000
    c = cart.Cart()
    c.add_item("expensive", 200, 6)  # subtotal =1200
    subtotal = c.subtotal()
    coupon_percent = cart.parse_coupon("SAVE30")
    discounted_amount = subtotal * (1 - coupon_percent / 100)
    shipping_fee = cart.shipping_fee(discounted_amount)  # member=False
    expected_total = round(discounted_amount + shipping_fee, 2)
    assert c.total(coupon="SAVE30") == expected_total

def test_cart_total_free_shipping_after_coupon_member():
    c = cart.Cart()
    c.add_item("expensive", 200, 6)  # subtotal =1200
    coupon_percent = cart.parse_coupon("SAVE30")
    discounted_amount = c.subtotal() * (1 - coupon_percent / 100)
    shipping_fee = cart.shipping_fee(discounted_amount, member=True)
    expected_total = round(discounted_amount + shipping_fee, 2)
    assert c.total(coupon="SAVE30", member=True) == expected_total

def test_cart_total_empty_with_coupon():
    c = cart.Cart()
    assert c.total(coupon="SAVE10") == 0.0
    assert c.total(coupon="SAVE10", member=True) == 0.0

def test_cart_total_invalid_coupon_raises_value_error():
    c = cart.Cart()
    c.add_item("item", 5, 1)
    with pytest.raises(ValueError):
        c.total(coupon="SAVEX")

def test_cart_total_with_complex_subtotal_and_discount():
    # Create subtotal that leads to fractional amounts after discount
    c = cart.Cart()
    c.add_item("test", 20.01, 5)   # subtotal =100.05 (no bulk discount)
    coupon_percent = cart.parse_coupon("SAVE30")
    discounted_amount = c.subtotal() * (1 - coupon_percent / 100)
    shipping_fee_non_member = cart.shipping_fee(discounted_amount)
    expected_total_non_member = round(discounted_amount + shipping_fee_non_member, 2)
    assert c.total(coupon="SAVE30") == expected_total_non_member

    shipping_fee_member = cart.shipping_fee(discounted_amount, member=True)
    expected_total_member = round(discounted_amount + shipping_fee_member, 2)
    assert c.total(coupon="SAVE30", member=True) == expected_total_member
