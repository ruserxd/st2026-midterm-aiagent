import pytest
import cart

# ---------- Tests for apply_discount ----------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0

@ pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- Tests for bulk_discount_percent ----------

def test_bulk_discount_percent_values():
    assert cart.bulk_discount_percent(1) == 0
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("quantity", [0, -1])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- Tests for parse_coupon ----------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    # case-insensitive and whitespace ignored per spec, but implementation may not
    assert cart.parse_coupon("save5 ") == 5
    assert cart.parse_coupon(" SAVE20 ") == 20

@ pytest.mark.parametrize("code", ["","SAVE0","SAVE51","BAD10","SAVExx","SAVE -1"]) 
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- Tests for shipping_fee ----------

def test_shipping_fee():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(5000) == 0
    # member gets half fee if subtotal < 1000
    assert cart.shipping_fee(200, member=True) == 30

@ pytest.mark.parametrize("subtotal", [-1])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Tests for Cart class ----------

def test_cart_basic_flow():
    c = cart.Cart()
    # subtotal should start at 0
    assert c.subtotal() == 0.0
    c.add_item("apple", unit_price=50, quantity=3)
    assert c.subtotal() == 150.0
    c.add_item("apple", unit_price=50, quantity=2)
    # subtotal should reflect increased quantity
    assert c.subtotal() == 250.0
    c.remove_item("apple", quantity=2)
    assert c.subtotal() == 100.0
    c.remove_item("apple", quantity=5)  # remove all
    assert c.subtotal() == 0.0


def test_cart_total_with_discounts_and_coupons():
    c = cart.Cart()
    c.add_item("tshirt", 200, 1)
    # no discount or coupon
    assert c.total(member=False) == pytest.approx(260.0)
    assert c.total(member=True) == pytest.approx(230.0)
    # coupon SAVE10 should reduce subtotal by 10%
    total_coupon = c.total(member=False, coupon="SAVE10")
    expected_subtotal = cart.apply_discount(200, 10)
    assert total_coupon == pytest.approx(expected_subtotal + 60.0)
    total_member_coupon = c.total(member=True, coupon="save10")
    assert total_member_coupon == pytest.approx(expected_subtotal + 30.0)

    # invalid coupon should raise ValueError
    with pytest.raises(ValueError):
        c.total(coupon="BAD10")

# ---------- Edge cases for Cart ----------

def test_cart_add_invalid_price_and_quantity():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("invalid", -5, 1)
    with pytest.raises(ValueError):
        c.add_item("zero_qty", 10, 0)


def test_cart_remove_nonexistent():
    c = cart.Cart()
    # Removing an item that does not exist should raise KeyError
    with pytest.raises(KeyError):
        c.remove_item("nonexist", quantity=1)
