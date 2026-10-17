import pytest
import cart

# ---- apply_discount tests ----

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0


def test_apply_discount_zero_percent():
    assert cart.apply_discount(100, 0) == 100.0


def test_apply_discount_full_percent():
    assert cart.apply_discount(250, 100) == 0.0


def test_apply_discount_rounding():
    # 99.999 with 10% -> 90.0001 => round to 2 decimals
    assert cart.apply_discount(99.999, 10) == 90.00

@ pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---- bulk_discount_percent tests ----

def test_bulk_discount_below_10():
    assert cart.bulk_discount_percent(9) == 0


def test_bulk_discount_between_10_and_49():
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(30) == 5


def test_bulk_discount_between_50_and_99():
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(75) == 10


def test_bulk_discount_above_100():
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(250) == 15

@ pytest.mark.parametrize("quantity", [0, -3])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---- parse_coupon tests ----

def test_parse_coupon_valid_cases():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon(" save25 ") == 25
    assert cart.parse_coupon("SaVe5") == 5

@ pytest.mark.parametrize("code", ["SAVe0", "SAVE51", "ABCD10", "save-5", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---- shipping_fee tests ----

def test_shipping_free_threshold():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500.5) == 0


def test_shipping_regular_and_member():
    assert cart.shipping_fee(500) == 60
    assert cart.shipping_fee(999.99, member=True) == 30

@ pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_negative_subtotal(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Cart tests ----

def test_cart_empty_total_and_subtotal():
    c = cart.Cart()
    assert c.subtotal() == 0
    assert c.total() == 0


def test_cart_add_and_remove_items_and_subtotal():
    c = cart.Cart()
    c.add_item("apple", 1.5, quantity=3)
    c.add_item("banana", 2.0)  # default qty 1
    assert c.subtotal() == 1.5 * 3 + 2.0
    c.remove_item("apple", quantity=2)
    # remaining apple count 1
    assert c.subtotal() == 1.5 * 1 + 2.0


def test_cart_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("widget", 200, quantity=5)   # subtotal 1000 -> shipping free before coupon
    # apply coupon SAVE10 (10% off)
    total = c.total(coupon="SAVE10")
    # After discount: 900, shipping free
    assert total == 900.00


def test_cart_total_with_member_and_coupon():
    c = cart.Cart()
    c.add_item("gadget", 300, quantity=2)   # subtotal 600 -> shipping 60 before coupon
    total = c.total(member=True, coupon="SAVE20")
    # After 20% off: 480, shipping 30 (member half)
    assert pytest.approx(total, rel=1e-9) == 480 + 30

# Ensure adding non-integer quantity raises ValueError via bulk_discount_percent

def test_cart_add_invalid_quantity_type():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("invalid", 10.0, quantity="two")
