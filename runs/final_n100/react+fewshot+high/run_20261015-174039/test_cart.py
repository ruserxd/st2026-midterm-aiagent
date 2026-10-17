import pytest
import cart

# Apply discount tests
def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price,percent,result", [
    (100, 0, 100.00),
    (200, 100, 0.00),
    (99, 33, round(99 * 67 / 100, 2))
])
def test_apply_discount_various(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# Bulk discount percent tests
@pytest.mark.parametrize("quantity,expected", [
    (5,0),(10,5),(49,5),(50,10),(99,10),(100,15),(150,15)
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("qty", [0, -1])
def test_bulk_discount_percent_nonpositive_raises(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

def test_bulk_discount_percent_float_quantity():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(10.5)

# Parse coupon tests
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    ("   SaVe30  ", 30)
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("invalid_code", ["SAVEBIG","SAVE0","SAVE51","ABC10","123","save-5"])
def test_parse_coupon_invalid(invalid_code):
    with pytest.raises(ValueError):
        cart.parse_coupon(invalid_code)

# Shipping fee tests
@pytest.mark.parametrize("subtotal,member,expected_fee", [
    (999.99, False, 60),
    (1000, False, 0),
    (500, True, 30)
])
def test_shipping_fee(subtotal, member, expected_fee):
    assert cart.shipping_fee(subtotal, member=member) == expected_fee

@pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_negative_subtotal_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart tests
def test_cart_initialization():
    c = cart.Cart()
    assert c.items() == {}

def test_add_item_new_and_increase_quantity():
    c = cart.Cart()
    c.add_item("apple", 5.0, 3)
    assert c.items() == {"apple": 3}
    # Add same item again with same price
    c.add_item("apple", 5.0, 2)
    assert c.items() == {"apple": 5}
    assert abs(c.subtotal() - 25.0) < 1e-9

def test_add_item_invalid_price_or_quantity():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("banana", -1.0, 2)
    with pytest.raises(ValueError):
        c.add_item("orange", 3.0, 0)
    with pytest.raises(ValueError):
        c.add_item("orange", 3.0, -5)

def test_add_item_price_mismatch():
    c = cart.Cart()
    c.add_item("pear", 4.0, 1)
    with pytest.raises(ValueError):
        c.add_item("pear", 5.0, 1)

def test_remove_item_partial_and_full():
    c = cart.Cart()
    c.add_item("apple", 2.0, 5)  # subtotal 10
    c.remove_item("apple", 3)
    assert c.items() == {"apple": 2}
    # Remove remaining quantity
    c.remove_item("apple", 2)
    assert "apple" not in c.items()

def test_remove_nonexistent_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("mango")

def test_items_returns_dict_of_quantities():
    c = cart.Cart()
    c.add_item("apple", 5.0, 3)
    c.add_item("banana", 2.0, 1)
    assert c.items() == {"apple": 3, "banana": 1}

def test_subtotal_empty_and_nonempty():
    c = cart.Cart()
    assert c.subtotal() == 0
    c.add_item("apple", 5.0, 3)   # subtotal 15
    c.add_item("banana", 2.0, 1) # +2 => 17
    assert c.subtotal() == 17.0

def test_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0

@pytest.mark.parametrize("items,coupon,member,expected", [
    ([("item", 500.0, 1)], None, False, 560.00),            # 500 + 60
    ([("item", 200.0, 1)], "SAVE10", False, 240.00),      # 180 + 60
    ([("item", 200.0, 1)], "SAVE10", True, 210.00),       # 180 + 30
    ([("item", 99.0, 1)], "SAVE5", False, 154.05),        # 94.05 + 60
    ([("item", 800.0, 1)], "SAVE10", False, 780.00),      # 720 + 60
    ([("item", 800.0, 1)], "SAVE10", True, 750.00),       # 720 + 30
    ([("item", 2000.0, 1)], "SAVE50", False, 1000.00),     # discounted 1000 + free shipping
])
def test_total_variants(items, coupon, member, expected):
    c = cart.Cart()
    for name, price, qty in items:
        c.add_item(name, price, qty)
    assert c.total(member=member, coupon=coupon) == pytest.approx(expected, rel=1e-9)

def test_total_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item("foo", 10.0, 1)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
