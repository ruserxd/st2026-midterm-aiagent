import pytest
import cart

SAMPLE_NAME = "Widget"
UNIT_PRICE = 100.0

# ---------- apply_discount ----------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent ----------

def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

@ pytest.mark.parametrize("quantity", [0, -3])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon(" save25 ") == 25
    assert cart.parse_coupon("SaVe50") == 50

@ pytest.mark.parametrize("code", ["SAV10", "SAVE0", "SAVE51", "ABCD"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------

def test_shipping_fee_free_and_member():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500, member=True) == 0

    assert cart.shipping_fee(500) == 60
    assert cart.shipping_fee(500, member=True) == 30

@ pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ----------

def test_cart_add_and_items():
    c = cart.Cart()
    assert c.items() == {}
    c.add_item(SAMPLE_NAME, UNIT_PRICE)
    assert c.items() == {SAMPLE_NAME: 1}
    c.add_item(SAMPLE_NAME, UNIT_PRICE, quantity=2)
    assert c.items() == {SAMPLE_NAME: 3}
    with pytest.raises(ValueError):
        c.add_item(SAMPLE_NAME, UNIT_PRICE + 10)

@ pytest.mark.parametrize("unit_price", [-1, -0.01])
def test_cart_add_negative_unit(unit_price):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("BadPrice", unit_price)

@ pytest.mark.parametrize("quantity", [0, -2])
def test_cart_add_invalid_quantity(quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item(SAMPLE_NAME, UNIT_PRICE, quantity=quantity)

def test_cart_remove():
    c = cart.Cart()
    c.add_item(SAMPLE_NAME, UNIT_PRICE, quantity=5)
    c.remove_item(SAMPLE_NAME, quantity=3)
    assert c.items() == {SAMPLE_NAME: 2}
    c.remove_item(SAMPLE_NAME, quantity=5)
    assert SAMPLE_NAME not in c.items()

def test_cart_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("NonExistent")

# ---------- subtotal calculation ----------

def test_subtotal_with_bulk_discount_and_rounding():
    c = cart.Cart()
    c.add_item("A", 10.0, quantity=5)
    assert c.subtotal() == 50.0
    c = cart.Cart()
    c.add_item("B", 20.0, quantity=10)  # 200 -> 190 after 5%
    assert c.subtotal() == 190.0
    c = cart.Cart()
    c.add_item("C1", 30.0, quantity=7)
    c.add_item("C2", 40.0, quantity=12)  # bulk 5%: 480*0.95=456
    assert c.subtotal() == round(210 + 456, 2)

# ---------- total calculation ----------

def test_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0

@ pytest.mark.parametrize("member", [False, True])
def test_total_no_coupon(member):
    c = cart.Cart()
    c.add_item(SAMPLE_NAME, 200.0, quantity=3)  # subtotal 600
    expected_shipping = 60 if not member else 30
    assert c.total(member=member) == round(600 + expected_shipping, 2)

def test_total_with_coupon():
    c = cart.Cart()
    c.add_item(SAMPLE_NAME, 1000.0, quantity=1)  # subtotal 1000 -> free shipping
    amount_after_coupon = 1000 * (1 - cart.parse_coupon("SAVE20")/100)
    expected_total = round(amount_after_coupon + cart.shipping_fee(1000), 2)
    assert c.total(coupon="SAVE20") == expected_total

def test_total_shipping_mismatch():
    c = cart.Cart()
    c.add_item(SAMPLE_NAME, 200.0, quantity=6)  # subtotal 1200
    amount_after_coupon = 1200 * 0.8
    shipping_on_correct = cart.shipping_fee(amount_after_coupon)
    expected_total_correct = round(amount_after_coupon + shipping_on_correct, 2)
    total_from_code = c.total(coupon="SAVE20")
    assert total_from_code != expected_total_correct
