import pytest
import cart

# ----------------------------
# apply_discount
# ----------------------------
def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(123.45, 50) == 61.72

@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [101, -5, 150])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ----------------------------
# bulk_discount_percent
# ----------------------------
def test_bulk_discount_basic():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(100) == 15

@pytest.mark.parametrize("qty", [0, -1])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ----------------------------
# parse_coupon
# ----------------------------
def test_parse_coupon_basic():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon(" save25 ") == 25
    assert cart.parse_coupon("SaVe1") == 1

@pytest.mark.parametrize("code", ["INVALID", "SAVE0", "SAVE51", "SAVEX"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ----------------------------
# shipping_fee
# ----------------------------
def test_shipping_fee_basic():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(500) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0
    # member discount
    assert cart.shipping_fee(300, member=True) == 30
    assert cart.shipping_fee(1200, member=True) == 0

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ----------------------------
# Cart operations
# ----------------------------
def test_cart_initially_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 0.0

def test_add_and_remove_items_basic():
    c = cart.Cart()
    c.add_item("apple", 100, 2)
    assert c.items() == {"apple": 2}
    # adding same item increases quantity
    c.add_item("apple", 100, 3)
    assert c.items() == {"apple": 5}
    # removing partial quantity
    c.remove_item("apple", 2)
    assert c.items() == {"apple": 3}
    # removing remaining brings to zero
    c.remove_item("apple", 3)
    assert c.items() == {}

def test_add_item_price_mismatch():
    c = cart.Cart()
    c.add_item("banana", 50, 1)
    with pytest.raises(ValueError):
        c.add_item("banana", 60, 1)  # price differs

@pytest.mark.parametrize("quantity", [0, -5])
def test_add_invalid_quantity(quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("orange", 30, quantity)

@pytest.mark.parametrize("unit_price", [-10, -1])
def test_add_negative_unit_price(unit_price):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("pear", unit_price, 1)

# subtotal calculations including bulk discounts

def test_subtotal_with_bulk_discount():
    c = cart.Cart()
    # 12 apples at 10 each -> 120; bulk discount 5% -> 114
    c.add_item("apple", 10, 12)
    assert c.subtotal() == 114.0
    # add 40 bananas at 20 each -> 800; bulk discount 10% -> 720
    c.add_item("banana", 20, 40)
    # total before rounding: 114 + 720 = 834
    assert c.subtotal() == 834.0

# total with coupon and shipping

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("widget", 100, 3)  # no bulk discount: subtotal 300
    # apply coupon SAVE10 -> 270; shipping fee 60 (not member)
    assert c.total(coupon="SAVE10") == 330.0
    # as member, shipping halves
    assert c.total(member=True, coupon="SAVE10") == 315.0

# total with free shipping threshold

def test_total_free_shipping():
    c = cart.Cart()
    c.add_item("luxury", 500, 3)  # subtotal 1500, no bulk discount
    # coupon SAVE20 -> 1200; shipping fee should be 0
    assert c.total(coupon="SAVE20") == 1200.0

# total with invalid coupon raises ValueError

def test_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("toy", 50, 1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# ensure empty cart has no shipping cost

def test_empty_cart_no_shipping():
    c = cart.Cart()
    assert c.total() == 0.0
