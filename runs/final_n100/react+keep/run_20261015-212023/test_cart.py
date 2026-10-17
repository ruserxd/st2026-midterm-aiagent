import pytest
import cart

# --------- apply_discount ----------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0

@ pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [ -5, 101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# --------- bulk_discount_percent ----------

def test_bulk_discount_percent_levels():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("qty", [0, -5])
def test_bulk_discount_percent_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# --------- parse_coupon ----------

def test_parse_coupon_valid_cases():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save5") == 5
    assert cart.parse_coupon("  Save20  ") == 20

@ pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "WRONG", "1234", "SAVE-1", " S A V E10 "])
def test_parse_coupon_invalid_cases(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --------- shipping_fee ----------

def test_shipping_fee_free_for_large_subtotal():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500, member=True) == 0

@ pytest.mark.parametrize("subtotal", [999.99, 500])
def test_shipping_fee_non_member(subtotal):
    assert cart.shipping_fee(subtotal, member=False) == 60

@ pytest.mark.parametrize("subtotal", [50, 800])
def test_shipping_fee_member(subtotal):
    assert cart.shipping_fee(subtotal, member=True) == 30

@ pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative_subtotal(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --------- Cart class ----------

def test_cart_add_and_remove_items():
    c = cart.Cart()
    assert c.items() == []
    c.add_item("apple", 100, quantity=2)
    assert c.items() == [("apple", 100, 2)]
    # Adding same item increases quantity
    c.add_item("apple", 100, quantity=3)
    assert c.items() == [("apple", 100, 5)]
    # Removing some quantity
    c.remove_item("apple", quantity=4)
    assert c.items() == [("apple", 100, 1)]
    # Removing more than existing removes the item entirely
    c.remove_item("apple", quantity=2)
    assert c.items() == []


def test_cart_subtotal_and_total_no_coupon_or_membership():
    c = cart.Cart()
    c.add_item("item1", 300, quantity=3)   # subtotal 900
    assert c.subtotal() == 900
    # Total without coupon: subtotal + shipping (60)
    assert c.total(member=False, coupon=None) == 960.0


def test_cart_total_with_coupon_and_member():
    c = cart.Cart()
    c.add_item("item2", 400, quantity=1)   # subtotal 400
    # Apply 10% discount via coupon "SAVE10"
    expected_after_coupon = cart.apply_discount(400, 10)
    # Shipping on discounted amount: member gets half of 60 -> 30
    expected_total = round(expected_after_coupon + 30, 2)
    assert c.total(member=True, coupon="SAVE10") == expected_total


def test_cart_total_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item("item3", 200)
    with pytest.raises(ValueError):
        c.total(member=False, coupon="BADCODE")


def test_empty_cart_total_zero():
    c = cart.Cart()
    assert c.total() == 0.0
