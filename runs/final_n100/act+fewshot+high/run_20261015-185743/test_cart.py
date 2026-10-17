import pytest
import cart

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

def test_apply_discount_rounding():
    # 123.456 * .9 = 111.1104 rounded to 2 decimals -> 111.11
    assert cart.apply_discount(123.456, 10) == pytest.approx(111.11)

@pytest.mark.parametrize("price,percent", [
    (-1, 20),
    (100, -5),
    (100, 105)
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

@pytest.mark.parametrize("quantity,expected_percent", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15)
])
def test_bulk_discount_percent(quantity, expected_percent):
    assert cart.bulk_discount_percent(quantity) == expected_percent

@pytest.mark.parametrize("quantity", [0, -1, "10", 5.5])
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

@pytest.mark.parametrize("code,expected_percent", [
    ("SAVE10", 10),
    ("save20", 20),
    ("  SAVE30  ", 30),
    ("sAvE40", 40)
])
def test_parse_coupon_valid(code, expected_percent):
    assert cart.parse_coupon(code) == expected_percent

@pytest.mark.parametrize("code", [
    "",
    "SAVEX",
    "save0",
    "SAVE51",
    "random code",
    "   "
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

def test_shipping_fee_non_member_free_threshold():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(999.99) == 60

def test_shipping_fee_member_half():
    assert cart.shipping_fee(1000, member=True) == 0
    assert cart.shipping_fee(999.99, member=True) == 30

def test_cart_add_item_basic():
    c = cart.Cart()
    c.add_item("Apple", 1.5, quantity=2)
    assert c.items() == {"Apple": 2}

    # Adding the same item increases its quantity
    c.add_item("Apple", 1.5, quantity=3)
    assert c.items() == {"Apple": 5}

def test_cart_add_item_price_mismatch():
    c = cart.Cart()
    c.add_item("Banana", 0.5, quantity=2)
    with pytest.raises(ValueError):
        c.add_item("Banana", 0.6)

@pytest.mark.parametrize("name,price,quantity", [
    ("Orange", -1, 3),
    ("Grape", 2, 0),
    ("Pear", 2, -1)
])
def test_cart_add_item_invalid_params(name, price, quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item(name, price, quantity)

@pytest.mark.parametrize("name,price,quantity", [
    ("Pear", 2, "3"),
    ("Mango", 1.5, 2.5)
])
def test_cart_add_item_nonint_quantity(name, price, quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item(name, price, quantity)

def test_cart_remove_item_reduce_quantity():
    c = cart.Cart()
    c.add_item("Mango", 2.0, quantity=5)
    c.remove_item("Mango", quantity=2)
    assert c.items() == {"Mango": 3}

def test_cart_remove_item_full_removal():
    c = cart.Cart()
    c.add_item("Mango", 2.0, quantity=5)
    c.remove_item("Mango", quantity=5)   # Remove all units
    assert "Mango" not in c.items()

def test_cart_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("Watermelon", quantity=1)

def test_cart_subtotal_no_discount():
    c = cart.Cart()
    c.add_item("Tea", 10, quantity=5)
    assert pytest.approx(c.subtotal(), rel=1e-9) == 50.0

def test_cart_subtotal_with_discounts():
    c = cart.Cart()
    # Coffee: 10 units, 5% bulk discount
    c.add_item("Coffee", 10, quantity=10)
    # Snack: 55 units, 10% bulk discount
    c.add_item("Snack", 5, quantity=55)
    assert pytest.approx(c.subtotal(), rel=1e-9) == 342.5

def test_cart_total_no_coupon_non_member():
    c = cart.Cart()
    c.add_item("Item1", 100, quantity=3)
    subtotal_expected = 300
    shipping_fee_expected = cart.shipping_fee(subtotal_expected)
    total_expected = round(subtotal_expected + shipping_fee_expected, 2)
    assert pytest.approx(c.total(member=False), rel=1e-9) == total_expected

def test_cart_total_with_coupon_non_member():
    c = cart.Cart()
    c.add_item("Item2", 200, quantity=1)
    discounted_amount = cart.apply_discount(200, 10)
    shipping_fee_expected = cart.shipping_fee(discounted_amount)
    total_expected = round(discounted_amount + shipping_fee_expected, 2)
    assert pytest.approx(c.total(member=False, coupon="SAVE10"), rel=1e-9) == total_expected

def test_cart_total_free_shipping_after_coupon():
    c = cart.Cart()
    # Expensive item: 6 units of $400 each
    c.add_item("Expensive", 400, quantity=6)
    discounted_amount = cart.apply_discount(2400, 10)
    shipping_fee_expected = cart.shipping_fee(discounted_amount)
    total_expected = round(discounted_amount + shipping_fee_expected, 2)
    assert pytest.approx(c.total(member=False, coupon="SAVE10"), rel=1e-9) == total_expected

def test_cart_total_member_half_shipping():
    c = cart.Cart()
    c.add_item("ItemX", 100, quantity=5)
    subtotal_expected = 500
    shipping_fee_expected = cart.shipping_fee(subtotal_expected, member=True)
    total_expected = round(subtotal_expected + shipping_fee_expected, 2)
    assert pytest.approx(c.total(member=True), rel=1e-9) == total_expected

def test_cart_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0.0

def test_cart_total_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item("Item", 100, quantity=1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCOUPON")

def test_cart_total_undercharging_due_to_bug_shipping():
    # Subtotal above threshold but discount brings it below; correct shipping should be applied
    c = cart.Cart()
    c.add_item("Item", 200, quantity=6)   # subtotal 1200
    discounted_amount = cart.apply_discount(1200, 20)
    shipping_fee_expected = cart.shipping_fee(discounted_amount)
    total_expected = round(discounted_amount + shipping_fee_expected, 2)
    assert pytest.approx(c.total(member=False, coupon="SAVE20"), rel=1e-9) == total_expected

def test_cart_total_member_undercharging_shipping():
    c = cart.Cart()
    c.add_item("Item", 200, quantity=6)   # subtotal 1200
    discounted_amount = cart.apply_discount(1200, 20)
    shipping_fee_expected = cart.shipping_fee(discounted_amount, member=True)
    total_expected = round(discounted_amount + shipping_fee_expected, 2)
    assert pytest.approx(c.total(member=True, coupon="SAVE20"), rel=1e-9) == total_expected
