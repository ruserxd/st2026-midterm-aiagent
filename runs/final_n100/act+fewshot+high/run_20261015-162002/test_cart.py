import pytest
import cart

# Specification constants for shipping
FREE_SHIPPING_THRESHOLD = 1000
BASE_FEE = 60

def expected_shipping(subtotal, member=False):
    if subtotal >= FREE_SHIPPING_THRESHOLD:
        return 0
    fee = BASE_FEE / 2 if member else BASE_FEE
    return fee

def expected_total(cart_obj, member=False, coupon=None):
    subtotal = cart_obj.subtotal()
    amount = subtotal
    if coupon is not None:
        percent = cart.parse_coupon(coupon)
        amount = cart.apply_discount(amount, percent)
    shipping_fee_val = expected_shipping(amount, member=member)
    return round(amount + shipping_fee_val, 2)

def test_apply_discount_basic():
    assert cart.apply_discount(200,15) == 170.0

@pytest.mark.parametrize("price,percent,expected", [
    (100,0,100.0),
    (100,100,0.0),
    (99.999,10,90.0),
    (10.555,5,10.03),   # 10.555*0.95=10.02725 round to 10.03
])
def test_apply_discount_cases(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

def test_apply_discount_errors():
    with pytest.raises(ValueError):
        cart.apply_discount(-1, 10)
    with pytest.raises(ValueError):
        cart.apply_discount(100, -5)
    with pytest.raises(ValueError):
        cart.apply_discount(100, 105)

@pytest.mark.parametrize("quantity,expected", [
    (1,0),
    (9,0),
    (10,5),
    (49,5),
    (50,10),   # spec: 10%
    (51,10),
    (99,10),
    (100,15),
    (150,15)
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("bad_qty", [0, -5, 3.5, "10"])
def test_bulk_discount_percent_errors(bad_qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(bad_qty)

@pytest.mark.parametrize("code,expected", [
    ("SAVE10",10),
    (" SAVE25 ",25),
    ("SaVe50",50),   # case-insensitive
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("invalid_code", [
    "SAVE0",
    "SAVE51",
    "ABC10",
    "",
    None,
    123
])
def test_parse_coupon_invalid(invalid_code):
    with pytest.raises(ValueError):
        cart.parse_coupon(invalid_code)

def test_shipping_fee_free():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0

def test_shipping_fee_base_and_member():
    assert cart.shipping_fee(500) == BASE_FEE
    assert cart.shipping_fee(999.99) == BASE_FEE
    assert cart.shipping_fee(500, member=True) == BASE_FEE / 2
    assert cart.shipping_fee(999.99, member=True) == BASE_FEE / 2

def test_shipping_fee_negative():
    with pytest.raises(ValueError):
        cart.shipping_fee(-1)

def test_cart_add_and_subtotal_no_bulk():
    c = cart.Cart()
    c.add_item("apple", 2.0, 3)
    assert c.items() == {"apple": 3}
    assert c.subtotal() == round(2.0*3, 2)

def test_cart_add_same_item_increments():
    c = cart.Cart()
    c.add_item("banana",1.5,2)
    c.add_item("banana",1.5,3)
    assert c.items()["banana"] == 5

def test_cart_add_different_price_error():
    c = cart.Cart()
    c.add_item("orange", 2.0, 1)
    with pytest.raises(ValueError):
        c.add_item("orange", 3.0, 1)

def test_cart_add_invalid_arguments():
    with pytest.raises(ValueError):
        cart.Cart().add_item("item", -5, 1)   # negative unit_price
    with pytest.raises(ValueError):
        cart.Cart().add_item("item", 5, 0)
    with pytest.raises(ValueError):
        cart.Cart().add_item("item", 5, -3)
    with pytest.raises(ValueError):
        cart.Cart().add_item("item", 5, 2.5)

def test_cart_remove_equal_quantity_bug():
    c = cart.Cart()
    c.add_item("widget", 10, 5)
    c.remove_item("widget", 5)
    assert "widget" not in c.items()

def test_cart_remove_partial_and_complete():
    c = cart.Cart()
    c.add_item("gadget", 20, 5)
    c.remove_item("gadget", 2)
    assert c.items()["gadget"] == 3
    c.remove_item("gadget", 3)
    assert "gadget" not in c.items()

def test_cart_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonitem", 1)

def test_cart_subtotal_bulk_discount():
    c = cart.Cart()
    c.add_item("widget", 10, 15)
    expected_line_total = round(10 * 15 * (1 - 0.05), 2)
    assert c.subtotal() == expected_line_total

def test_cart_subtotal_multiple_items():
    c = cart.Cart()
    c.add_item("A", 10, 5)   # no discount
    c.add_item("B", 20, 15)  # bulk discount 5%
    subtotal_a = round(10 * 5, 2)
    line_b_total = round(20 * 15 * (1 - 0.05), 2)
    expected_total = round(subtotal_a + line_b_total, 2)
    assert c.subtotal() == expected_total

def test_cart_subtotal_empty():
    c = cart.Cart()
    assert c.subtotal() == 0

def test_cart_total_no_coupon_non_member():
    c = cart.Cart()
    c.add_item("item", 2.0, 3)
    expected = round(6 + BASE_FEE, 2)
    assert c.total() == expected

def test_cart_total_no_coupon_member():
    c = cart.Cart()
    c.add_item("item", 2.0, 3)
    expected = round(6 + BASE_FEE/2, 2)
    assert c.total(member=True) == expected

def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0

def test_cart_total_with_coupon_below_threshold():
    c = cart.Cart()
    c.add_item("Laptop", 200, 6)
    expected_value = expected_total(c, member=False, coupon="SAVE20")
    actual_value = c.total(member=False, coupon="SAVE20")
    assert actual_value == expected_value

def test_cart_total_with_coupon_below_threshold_member():
    c = cart.Cart()
    c.add_item("Laptop", 200, 6)
    expected_value = expected_total(c, member=True, coupon="SAVE20")
    actual_value = c.total(member=True, coupon="SAVE20")
    assert actual_value == expected_value

def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("item", 5.0, 1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
