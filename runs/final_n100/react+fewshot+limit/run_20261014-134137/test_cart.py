import pytest
import cart

# ---------- apply_discount ---------------------------------

def test_apply_discount_basic():
    # simple discount
    assert cart.apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize("price, percent, expected", [
    (100, 0, 100.0),        # no discount
    (123.45, 50, 61.725),   # half off
])
def test_apply_discount_various(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# boundaries for percent and price
@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_price_negative(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_percent_out_of_range(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent ----------------------------

def test_bulk_discount_percent_levels():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

@pytest.mark.parametrize("qty", [0, -1])
def test_bulk_discount_percent_invalid_quantity(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- parse_coupon -------------------------------------

def test_parse_coupon_valid_cases():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save25") == 25
    assert cart.parse_coupon(" SAVE5 ") == 5

@pytest.mark.parametrize("code", ["SAVEX", "save0", "save51", "sAvE-1", ""])
def test_parse_coupon_invalid_cases(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee -------------------------------------

def test_shipping_fee_basic():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(999.99) == 60

assertion_member = pytest.mark.parametrize("subtotal", [0, 500])
@ assertion_member
def test_shipping_fee_member(subtotal):
    assert cart.shipping_fee(subtotal, member=True) == 30

@pytest.mark.parametrize("subtotal", [-10, -1.5])
def test_shipping_fee_negative_subtotal(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ---------------------------------------

def test_cart_initially_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

@ pytest.mark.parametrize("name, unit_price, qty", [
    ("apple", 2.0, 3),
])
def test_cart_add_item(name, unit_price, qty):
    c = cart.Cart()
    c.add_item(name, unit_price, qty)
    assert c.items() == {name: qty}
    # subtotal should apply bulk discount if applicable
    expected_line_total = unit_price * qty
    expected_subtotal = cart.apply_discount(expected_line_total, cart.bulk_discount_percent(qty))
    assert c.subtotal() == round(expected_subtotal, 2)

# adding same item increases quantity
@ pytest.mark.parametrize("name, price, first_qty, second_qty", [
    ("banana", 1.5, 2, 3),
])
def test_cart_add_existing(name, price, first_qty, second_qty):
    c = cart.Cart()
    c.add_item(name, price, first_qty)
    with pytest.raises(ValueError):
        # mismatched unit price
        c.add_item(name, price + 0.1, 1)
    c.add_item(name, price, second_qty)
    assert c.items()[name] == first_qty + second_qty

# invalid add tests
@pytest.mark.parametrize("unit_price", [-5])
def test_cart_add_negative_unit_price(unit_price):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("x", unit_price)

@pytest.mark.parametrize("qty", [0, -2])
def test_cart_add_invalid_quantity(qty):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("y", 10.0, qty)

# remove item tests
@ pytest.mark.parametrize("name, unit_price, qty", [
    ("milk", 3.0, 4),
])
def test_cart_remove_item(name, unit_price, qty):
    c = cart.Cart()
    c.add_item(name, unit_price, qty)
    c.remove_item(name, 2)
    assert c.items()[name] == 2
    # remove remaining to delete item
    c.remove_item(name, 2)
    assert name not in c.items()

@pytest.mark.parametrize("name", ["nonexistent"])
def test_cart_remove_nonexistent(name):
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item(name)

# subtotal rounding and bulk discount
def test_cart_subtotal_bulk_and_rounding():
    c = cart.Cart()
    # 12 units of item priced 10 -> bulk discount 5%
    c.add_item("item1", 10.0, 12)
    line_total = 10.0 * 12
    discounted = cart.apply_discount(line_total, cart.bulk_discount_percent(12))
    assert c.subtotal() == round(discounted, 2)

# total with coupon and member shipping fee discrepancy test

def test_cart_total_with_coupon_and_member():
    c = cart.Cart()
    c.add_item("item", 100.0, 1)  # subtotal 100
    # coupon 10% -> amount should be 90
    total_expected = round(90 + cart.shipping_fee(90, member=True), 2)
    assert c.total(member=True, coupon="SAVE10") == total_expected

# test that total ignores coupon for shipping fee as per implementation

def test_cart_total_shipping_fee_on_original_subtotal():
    c = cart.Cart()
    c.add_item("item", 100.0, 1)
    # subtotal is 100, shipping fee for non-member is 60 regardless of coupon
    amount_after_discount = cart.apply_discount(100, cart.parse_coupon("SAVE10"))
    total_expected = round(amount_after_discount + cart.shipping_fee(100), 2)
    assert c.total(coupon="SAVE10") == total_expected
