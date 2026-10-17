import pytest
import cart

# ---------- apply_discount ----------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101, 150])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent ----------

def test_bulk_discount_percent_ranges():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@pytest.mark.parametrize("quantity", [0, -1, 2.5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------

def test_parse_coupon_valid_cases():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save50") == 50
    assert cart.parse_coupon(" SAVE25 ") == 25
    # case-insensitive with spaces
    assert cart.parse_coupon(" SaVe15 ") == 15

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "SAVEE10", "XYZ10", "save-5", "", "   "])
def test_parse_coupon_invalid_codes(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------

def test_shipping_fee_free_and_regular():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(500) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(2000) == 0

def test_shipping_fee_member_half():
    assert cart.shipping_fee(0, member=True) == 30
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(1000, member=True) == 0

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid_subtotal(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class operations ----------

def test_cart_add_and_items():
    c = cart.Cart()
    assert c.items() == {}
    c.add_item("apple", 1.00, 3)
    assert c.items() == {"apple": 3}
    # Adding same item increases quantity
    c.add_item("apple", 1.00, 2)
    assert c.items() == {"apple": 5}

@pytest.mark.parametrize("unit_price,quantity", [( -1, 1), (0.99, 0), (1.00, -3)])
def test_cart_add_invalid(unit_price, quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("banana", unit_price, quantity)

@pytest.mark.parametrize("name,unit_price,quantity", [("pear", 1.50, 1), ("pear", 2.00, 1)])
def test_cart_add_different_unit_prices(name, unit_price, quantity):
    c = cart.Cart()
    c.add_item(name, 1.00)
    # attempting to add same name with different price
    with pytest.raises(ValueError):
        c.add_item(name, unit_price, quantity)

def test_cart_remove():
    c = cart.Cart()
    c.add_item("orange", 0.80, 5)
    c.remove_item("orange", 3)
    assert c.items() == {"orange": 2}
    # remove more than present, item removed
    c.remove_item("orange", 5)
    assert "orange" not in c.items()

@pytest.mark.parametrize("name", ["nonexistent"])
def test_cart_remove_nonexistent(name):
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item(name, 1)

# ---------- Cart.subtotal ----------

def test_cart_subtotal_no_bulk():
    c = cart.Cart()
    c.add_item("item", 10.00, 9)  # no bulk discount
    assert c.subtotal() == 90.0

def test_cart_subtotal_with_bulk():
    c = cart.Cart()
    c.add_item("bulk", 5.00, 10)  # 5% discount per item
    # discounted unit price: 5 * 0.95 = 4.75; total = 47.5
    assert c.subtotal() == 47.5
    c.add_item("big", 20.00, 50)  # 10% bulk discount
    # big item subtotal after discount: 20*0.9*50=900
    # total subtotal: 47.5 + 900 = 947.5
    assert c.subtotal() == 947.5

# ---------- Cart.total ----------

def test_cart_total_no_coupon_member():
    c = cart.Cart()
    c.add_item("widget", 1000, 1)
    # subtotal 1000 -> no shipping
    assert c.total(member=False) == 1000.00

    c.add_item("extra", 200, 2)  # 400 total without discount
    # subtotal: 1400, shipping free
    assert c.total() == 1400.00

def test_cart_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("pencil", 1.50, 10)  # bulk 5% -> unit 1.425 -> subtotal 14.25
    # apply coupon SAVE10 => 10%
    total_before_shipping = round(14.25 * 0.9, 2)
    assert c.total(coupon="SAVE10") == total_before_shipping + cart.shipping_fee(total_before_shipping)

    # member gets half shipping
    total_member = round(total_before_shipping * 1, 2)  # no discount after coupon already applied
    expected = round(total_before_shipping + cart.shipping_fee(total_before_shipping, member=True), 2)
    assert c.total(member=True, coupon="SAVE10") == expected

# ---------- Edge cases for total empty cart ----------

def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0.00
    # coupon or member should still give 0
    assert c.total(member=True, coupon="SAVE10") == 0.00

# ---------- Invalid coupon in total ----------

def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("item", 100, 1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
