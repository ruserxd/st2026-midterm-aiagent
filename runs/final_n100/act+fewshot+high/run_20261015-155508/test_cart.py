import pytest
import cart

# Apply discount tests
@pytest.mark.parametrize("price, percent, expected", [
    (200, 15, 170.0),
    (100, 33, 67.0),
    (1234, 12, round(1234 * 0.88, 2)),
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price", [-10, -1e-6])
def test_apply_discount_invalid_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# Bulk discount percent tests
@pytest.mark.parametrize("quantity, expected", [
    (1, 0),
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

@pytest.mark.parametrize("quantity", [0, -1, 2.5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# Parse coupon tests
@pytest.mark.parametrize("code, expected", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30)
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["", "1234", "SAVEX", " SAVE0 ", "SAVE51"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Shipping fee tests
@pytest.mark.parametrize("subtotal, member, expected_fee", [
    (500, False, 60),
    (999.99, True, 30),
    (1000, False, 0),
    (1500, True, 0)
])
def test_shipping_fee(subtotal, member, expected_fee):
    assert cart.shipping_fee(subtotal, member) == expected_fee

@pytest.mark.parametrize("subtotal", [-10, -1e-6])
def test_shipping_fee_invalid_subtotal(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart tests
def test_cart_add_new_item():
    c = cart.Cart()
    c.add_item("apple", 1.0)
    assert c.items() == {"apple": 1}

def test_cart_add_existing_same_price_increases_quantity():
    c = cart.Cart()
    c.add_item("banana", 2.5, quantity=3)
    c.add_item("banana", 2.5, quantity=2)
    assert c.items() == {"banana": 5}

def test_cart_add_existing_different_price_raises_value_error():
    c = cart.Cart()
    c.add_item("orange", 1.0)
    with pytest.raises(ValueError):
        c.add_item("orange", 1.5)

def test_cart_remove_partial():
    c = cart.Cart()
    c.add_item("pear", 3, quantity=4)
    c.remove_item("pear", quantity=2)
    assert c.items() == {"pear": 2}

def test_cart_remove_exact_removal():
    c = cart.Cart()
    c.add_item("kiwi", 0.5, quantity=1)
    c.remove_item("kiwi", quantity=1)
    assert c.items() == {}

def test_cart_remove_more_than_current_deletes():
    c = cart.Cart()
    c.add_item("melon", 2, quantity=2)
    c.remove_item("melon", quantity=3)  # more than present
    assert c.items() == {}

def test_cart_remove_nonexistent_raises_key_error():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent")

def test_cart_items_dict_keys_and_values_only():
    c = cart.Cart()
    c.add_item("mango", 1.2, quantity=5)
    assert set(c.items().keys()) == {"mango"}
    assert c.items()["mango"] == 5

# Subtotal tests
def test_subtotal_no_discount():
    c = cart.Cart()
    c.add_item("bread", 2.0, quantity=3)  # <10, no discount
    assert c.subtotal() == 6.0

def test_subtotal_with_bulk_discount_5_percent():
    c = cart.Cart()
    c.add_item("cheese", 5.0, quantity=12)  # >=10 => 5% discount
    expected_line_total = 5.0 * 12
    discounted = round(expected_line_total * 0.95, 2)
    assert c.subtotal() == discounted

def test_subtotal_with_bulk_discount_15_percent():
    c = cart.Cart()
    c.add_item("chips", 1.5, quantity=120)  # >=100 => 15% discount
    expected_line_total = 1.5 * 120
    discounted = round(expected_line_total * 0.85, 2)
    assert c.subtotal() == discounted

def test_subtotal_rounding():
    c = cart.Cart()
    c.add_item("spice", 3.33, quantity=11)  # >=10 => 5% discount
    line_total = 3.33 * 11
    discounted = round(line_total * 0.95, 2)
    assert c.subtotal() == discounted

# Total tests
def test_total_no_coupon_non_member():
    c = cart.Cart()
    c.add_item("item", 50, quantity=1)
    expected_subtotal = 50
    expected_fee = 60 if expected_subtotal < 1000 else 0
    assert c.total() == round(expected_subtotal + expected_fee, 2)

def test_total_no_coupon_member():
    c = cart.Cart()
    c.add_item("item", 75, quantity=1)
    subtotal = 75
    fee = 30 if subtotal < 1000 else 0
    assert c.total(member=True) == round(subtotal + fee, 2)

def test_total_with_coupon_non_member():
    c = cart.Cart()
    c.add_item("item", 200, quantity=1)
    amount_after_discount = cart.apply_discount(200, 10)  # 180
    shipping = 60 if amount_after_discount < 1000 else 0
    assert c.total(coupon="SAVE10") == round(amount_after_discount + shipping, 2)

def test_total_with_coupon_member():
    c = cart.Cart()
    c.add_item("item", 300, quantity=1)
    amount_after_discount = cart.apply_discount(300, 15)  # 255
    shipping = 30 if amount_after_discount < 1000 else 0
    assert c.total(member=True, coupon="SAVE15") == round(amount_after_discount + shipping, 2)

def test_total_coupon_affects_shipping():
    # subtotal > 1000 but discount brings it below threshold
    c = cart.Cart()
    c.add_item("big", 1200, quantity=1)  # subtotal 1200
    amount_after_discount = cart.apply_discount(1200, 20)  # 960
    shipping_fee_expected = 60  # non-member
    expected_total = round(amount_after_discount + shipping_fee_expected, 2)
    assert c.total(coupon="SAVE20") == expected_total

def test_total_coupon_affects_shipping_member():
    c = cart.Cart()
    c.add_item("big", 1200, quantity=1)
    amount_after_discount = cart.apply_discount(1200, 25)  # 900
    shipping_fee_expected = 30
    expected_total = round(amount_after_discount + shipping_fee_expected, 2)
    assert c.total(member=True, coupon="SAVE25") == expected_total

def test_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0
