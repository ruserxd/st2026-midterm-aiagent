import pytest
import cart

# Fixtures
@pytest.fixture
def empty_cart():
    return cart.Cart()

@pytest.fixture
def sample_cart():
    c = cart.Cart()
    c.add_item("pear", 1.50, 5)
    return c

# apply_discount tests
@pytest.mark.parametrize("price, percent, expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
    (19.99, 10, 17.99),  # round to 2 decimals
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize("quantity, expected", [
    (5, 0),
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

@pytest.mark.parametrize("quantity", [0, -1, -5, "10"])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize("code, percent", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
    ("SaVe5", 5),
])
def test_parse_coupon_valid(code, percent):
    assert cart.parse_coupon(code) == percent

@pytest.mark.parametrize("invalid_code", [
    "SAV10",
    "SAVE0",
    "SAVE51",
    "SAVE-1",
    "SAVE10A",
    "ABCD10",
    "",
    "   ",
])
def test_parse_coupon_invalid(invalid_code):
    with pytest.raises(ValueError):
        cart.parse_coupon(invalid_code)

@pytest.mark.parametrize("code", [123, None, 5.5])
def test_parse_coupon_nonstring(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal, member, expected", [
    (1000, False, 0),
    (1000, True, 0),
    (999.99, False, 60),
    (999.99, True, 30),
    (0, False, 60),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart methods tests
def test_add_item_new(empty_cart):
    empty_cart.add_item("apple", 1.00, 2)
    assert empty_cart.items() == {"apple": 2}

def test_add_item_increment(empty_cart):
    empty_cart.add_item("banana", 0.5, 3)
    empty_cart.add_item("banana", 0.5, 2)
    assert empty_cart.items()["banana"] == 5

def test_add_item_price_mismatch(empty_cart):
    empty_cart.add_item("orange", 1.00, 1)
    with pytest.raises(ValueError):
        empty_cart.add_item("orange", 1.50, 1)

@pytest.mark.parametrize("price", [-0.01])
def test_add_item_negative_price(price):
    cart_obj = cart.Cart()
    with pytest.raises(ValueError):
        cart_obj.add_item("mango", price, 1)

@pytest.mark.parametrize("quantity", [0, -2, 3.5, "4"])
def test_add_item_invalid_quantity(quantity):
    cart_obj = cart.Cart()
    with pytest.raises(ValueError):
        cart_obj.add_item("grape", 2.00, quantity)

# Remove item tests
def test_remove_partial(sample_cart):
    sample_cart.remove_item("pear", 3)
    assert sample_cart.items()["pear"] == 2

def test_remove_exact(sample_cart):
    # remove all remaining (5) in two steps
    sample_cart.remove_item("pear", 5)
    assert "pear" not in sample_cart.items()

def test_remove_more_than_exists(sample_cart):
    # After removal of more than existing, should delete item
    sample_cart.remove_item("pear", 10)
    assert "pear" not in sample_cart.items()

def test_remove_nonexistent(empty_cart):
    with pytest.raises(KeyError):
        empty_cart.remove_item("nonexistent")

# items returns a new dict
def test_items_return_new_dict():
    c = cart.Cart()
    c.add_item("apple", 1, 2)
    d = c.items()
    assert d == {"apple": 2}
    d["apple"] = 5
    # Internal state should remain unchanged
    assert c.items()["apple"] == 2

# subtotal tests
def test_subtotal_empty(empty_cart):
    assert empty_cart.subtotal() == 0

@pytest.mark.parametrize("unit_price, quantity, expected", [
    (10.00, 3, 30.00),  # no discount
])
def test_subtotal_no_discount(unit_price, quantity, expected):
    c = cart.Cart()
    c.add_item("testitem", unit_price, quantity)
    assert c.subtotal() == expected

@pytest.mark.parametrize("unit_price, quantity, percent, expected", [
    (20.00, 10, 5, 190.00),   # 200 - 5% = 190
    (10.00, 50, 10, 450.00),  # 500 -10% = 450
    (15.00, 100, 15, 1275.00) # 1500 -15% = 1275
])
def test_subtotal_with_discount(unit_price, quantity, percent, expected):
    c = cart.Cart()
    c.add_item("testitem", unit_price, quantity)
    assert c.subtotal() == expected

# Test rounding behavior
def test_subtotal_rounding():
    c = cart.Cart()
    c.add_item("foo", 19.99, 3)
    # 19.99 * 3 = 59.97 exactly
    assert c.subtotal() == round(19.99 * 3, 2)

# total tests
def test_total_empty(empty_cart):
    assert empty_cart.total() == 0

@pytest.mark.parametrize("unit_price, quantity, member, expected", [
    # subtotal after bulk discount: 10 units of $20 -> 190
    (20.00, 10, False, round(190.00 + 60, 2)),
])
def test_total_no_coupon(unit_price, quantity, member, expected):
    c = cart.Cart()
    c.add_item("test", unit_price, quantity)
    assert c.total(member=member) == expected

@pytest.mark.parametrize("unit_price, quantity, member, expected", [
    # 100 units of $20 -> subtotal 1700 (after bulk discount), shipping free
    (20.00, 100, False, round(1700 + 0, 2)),
])
def test_total_free_shipping(unit_price, quantity, member, expected):
    c = cart.Cart()
    c.add_item("test", unit_price, quantity)
    assert c.total(member=member) == expected

@pytest.mark.parametrize("unit_price, quantity, coupon, member, expected", [
    # subtotal 190 after bulk discount; coupon SAVE20 -> amount 152; shipping on 152
    (20.00, 10, "SAVE20", False, round(152.00 + 60, 2)),
    (20.00, 10, "SAVE20", True, round(152.00 + 30, 2))
])
def test_total_with_coupon(unit_price, quantity, coupon, member, expected):
    c = cart.Cart()
    c.add_item("test", unit_price, quantity)
    assert c.total(member=member, coupon=coupon) == expected

# Test that invalid coupon raises ValueError in total
@pytest.mark.parametrize("coupon", ["BADCODE", "SAV10"])
def test_total_invalid_coupon(empty_cart, coupon):
    empty_cart.add_item("item", 10, 1)
    with pytest.raises(ValueError):
        empty_cart.total(coupon=coupon)
