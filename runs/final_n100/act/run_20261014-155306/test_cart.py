import cart
import pytest

# ---------- apply_discount ----------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(0, 50) == 0.0

@ pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [-1, -0.5, 101, 150])
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

@ pytest.mark.parametrize("quantity", [0, -5, 3.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon("  SaVe30 ") == 30

@ pytest.mark.parametrize(
    "code",
    ["", "SAVE", "SAVExx", "SAVE51", "DISCOUNT5", "save-10"]
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------

def test_shipping_fee():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(2000) == 0

@ pytest.mark.parametrize("subtotal", [-1, -5])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart total logic ----------

def test_cart_empty_total():
    c = cart.Cart()
    assert c.total() == 0
    assert c.total(member=True) == 0


def test_cart_add_and_subtotal():
    c = cart.Cart()
    c.add_item("apple", 2.5, quantity=4)
    c.add_item("banana", 1.0)
    assert c.subtotal() == pytest.approx(11.0)  # 4*2.5 + 1*1


def test_cart_remove_and_items():
    c = cart.Cart()
    c.add_item("apple", 3, quantity=5)
    c.remove_item("apple", quantity=2)
    assert len(c.items()) == 1
    assert c.items()[0]["quantity"] == 3

# Simple coupon application test

def test_cart_total_with_coupon_and_member():
    c = cart.Cart()
    c.add_item("item", 200, quantity=5)  # subtotal 1000
    # No shipping because subtotal >= 1000
    assert c.total() == 1000.0
    # Apply coupon 20% off; new amount 800 + shipping 60
    total_with_coupon = c.total(coupon="SAVE20")
    expected_after_discount = cart.apply_discount(1000, 20)  # 800.0
    expected_shipping = cart.shipping_fee(expected_after_discount)
    assert total_with_coupon == pytest.approx(expected_after_discount + expected_shipping)

# Test invalid coupon raises ValueError

def test_cart_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item("item", 50, quantity=1)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
