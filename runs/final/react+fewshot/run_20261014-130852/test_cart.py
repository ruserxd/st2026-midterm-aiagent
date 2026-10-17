import pytest
import cart

# --- discount functions ---

def test_apply_discount_valid():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0

@ pytest.mark.parametrize("price,percent", [(-1,10), (100,-5), (100,105)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --- bulk discount percent ---

def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

@ pytest.mark.parametrize("quantity", [0, -1, 2.5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --- coupon parsing ---

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon("   SaVe5   ") == 5

@ pytest.mark.parametrize("code", ["INVALID", "SAVExx", "SAVE0", "SAVE51", "SAVEX"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping fee ---

def test_shipping_fee():
    assert cart.shipping_fee(999) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(2000) == 0
    # member flag
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(1200, member=True) == 0

@ pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --- Cart class ---

def test_cart_add_and_items():
    c = cart.Cart()
    assert c.items() == {}
    c.add_item("apple", 1.0, 2)
    assert c.items() == {"apple": 2}
    # adding same item increases quantity
    c.add_item("apple", 1.0, 3)
    assert c.items() == {"apple": 5}
    # different item
    c.add_item("banana", 0.5, 4)
    assert c.items() == {"apple": 5, "banana": 4}

@ pytest.mark.parametrize("name,price,quantity", [
    ("pear", -1, 2),
    ("pear", 1.0, 0),
    ("pear", 1.0, -3),
])
def test_cart_add_errors(name, price, quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item(name, price, quantity)

@ pytest.mark.parametrize("name,price,quantity", [
    ("pear", 1.0, 2),
])
def test_cart_add_price_mismatch(name, price, quantity):
    c = cart.Cart()
    c.add_item(name, price, quantity)
    with pytest.raises(ValueError):
        c.add_item(name, price + 0.5, 1)

# removal tests

def test_cart_remove_and_quantity():
    c = cart.Cart()
    c.add_item("orange", 2.0, 5)
    c.remove_item("orange", 3)
    assert c.items() == {"orange": 2}
    # removing remaining brings to zero
    c.remove_item("orange", 2)
    assert c.items() == {}
    # removing more than present should remove entirely
    c.add_item("grape", 0.3, 1)
    c.remove_item("grape", 5)
    assert c.items() == {}

@ pytest.mark.parametrize("name", ["nonexistent"])
def test_cart_remove_missing(name):
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item(name, 1)

# subtotal tests with bulk discounts

def test_subtotal_bulk_discount():
    c = cart.Cart()
    # no items
    assert c.subtotal() == 0
    # add 10 apples at $1 each -> bulk discount 5%
    c.add_item("apple", 1.0, 10)
    expected = round(1.0 * 10 * (1 - 0.05), 2)
    assert c.subtotal() == expected
    # add 60 bananas at $0.5 -> bulk discount 10%
    c.add_item("banana", 0.5, 60)
    banana_cost = round(0.5 * 60 * (1 - 0.10), 2)
    apple_cost = round(1.0 * 10 * (1 - 0.05), 2)
    assert c.subtotal() == round(apple_cost + banana_cost, 2)

# total with coupon and shipping

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("item", 100.0, 1)  # subtotal 100
    # no coupon, non-member -> shipping 60
    assert c.total() == round(100 + 60, 2)
    # member flag halves shipping
    assert c.total(member=True) == round(100 + 30, 2)
    # with valid coupon SAVE10 reduces by 10%
    expected_after_coupon = round(100 * (1 - 0.10), 2)
    total_with_coupon = c.total(coupon="SAVE10")
    assert total_with_coupon == round(expected_after_coupon + cart.shipping_fee(expected_after_coupon, member=False), 2)

# test coupon invalid raises ValueError in total

def test_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("item", 50.0, 1)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
