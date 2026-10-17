import pytest
import cart

# --- discount helpers -----------------------------------------------------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# invalid values
@pytest.mark.parametrize("price,percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --- bulk discount --------------------------------------------------------
@pytest.mark.parametrize("quantity,percent", [
    (9, 0), (10, 5), (49, 5), (50, 10), (99, 10), (100, 15), (150, 15)
])
def test_bulk_discount_percent(quantity, percent):
    assert cart.bulk_discount_percent(quantity) == percent

# invalid quantity
@pytest.mark.parametrize("quantity", [0, -5, 2.3])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --- coupon parsing -------------------------------------------------------
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    ("save5", 5),
    ("   SaVe20  ", 20),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", [
    "NOSAVE", "SAVE0", "SAVE51", "SAVEXX", " SAVE-10 ", ""
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping fee --------------------------------------------------------
@pytest.mark.parametrize("subtotal,member,fee", [
    (0, False, 60),
    (999.99, True, 30),
    (1000, False, 0),
])
def test_shipping_fee(subtotal, member, fee):
    assert cart.shipping_fee(subtotal, member) == fee

# invalid subtotal
@pytest.mark.parametrize("subtotal", [-1, -50.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --- Cart behavior -------------------------------------------------------
@pytest.fixture
def empty_cart():
    return cart.Cart()

def test_cart_initial_state(empty_cart):
    assert empty_cart.items() == {}
    assert empty_cart.subtotal() == 0.0
    assert empty_cart.total() == 0.0

# adding items and subtotal calculation with bulk discount

def test_add_and_subtotal():
    c = cart.Cart()
    c.add_item("apple", unit_price=100, quantity=5)   # no discount
    assert c.subtotal() == 500.0
    c.add_item("banana", unit_price=200, quantity=12)  # 5% discount on bananas
    # banana subtotal: 200*12 = 2400; 5% -> 2280
    assert c.subtotal() == round(500 + 2280, 2)

# adding same item with different price should raise

def test_add_same_item_different_price():
    c = cart.Cart()
    c.add_item("item", unit_price=50, quantity=1)
    with pytest.raises(ValueError):
        c.add_item("item", unit_price=60, quantity=2)

# remove items and automatic deletion

def test_remove_items():
    c = cart.Cart()
    c.add_item("gadget", 300, quantity=3)
    c.remove_item("gadget", quantity=1)
    assert c.items() == {"gadget": 2}
    c.remove_item("gadget", quantity=2)
    assert c.items() == {}

# removing non-existent item raises KeyError

def test_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("unknown")

# total calculation with coupon and shipping, member status

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    # 1000 + 200*10=2000 -> subtotal 3000; bulk discount on banana (10 units) => 5% -> 1900
    c.add_item("banana", unit_price=200, quantity=10)
    subtotal_expected = round(200*10 * 0.95, 2)  # 1900
    assert c.subtotal() == subtotal_expected
    # apply coupon SAVE20 => 20% off
    total_after_coupon = cart.apply_discount(subtotal_expected, 20)
    # shipping on amount after coupon: subtotal 1520 >1000 so free
    expected_total = round(total_after_coupon + 0, 2)
    assert c.total(coupon="SAVE20") == expected_total

# total for empty cart should be 0 and no shipping

def test_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0.0
