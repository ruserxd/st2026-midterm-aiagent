import pytest
import cart

# Helper for floating comparison

def approx(value, expected):
    return pytest.approx(expected, rel=1e-12)

# ------------------- apply_discount -------------------

def test_apply_discount_normal():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0

@ pytest.mark.parametrize("price", [-1, -10])
@ pytest.mark.parametrize("percent", [20])
def test_apply_discount_price_negative(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

@ pytest.mark.parametrize("percent", [-5, 105])
@ pytest.mark.parametrize("price", [100])
def test_apply_discount_percent_out_of_range(percent, price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ------------------- bulk_discount_percent -------------------

def test_bulk_discount_percent_values():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(100) == 15

@ pytest.mark.parametrize("quantity", [-1, 0])
def test_bulk_discount_negative(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ------------------- parse_coupon -------------------

def test_parse_coupon_valid_cases():
    assert cart.parse_coupon('SAVE10') == 10
    assert cart.parse_coupon('save20') == 20
    assert cart.parse_coupon(' SAVE30 ') == 30

@ pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "ABC12", "123"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ------------------- shipping_fee -------------------

def test_shipping_fee_standard():
    assert cart.shipping_fee(500) == 60
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60

def test_shipping_fee_member():
    assert cart.shipping_fee(200, member=True) == 30
    assert cart.shipping_fee(0, member=True) == 30

@ pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ------------------- Cart basic operations -------------------

def test_cart_initially_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 0.0

def test_add_and_remove_items():
    c = cart.Cart()
    c.add_item('apple', 1.0, 3)
    assert c.items() == {'apple': 3}
    # adding same item increases quantity, same unit price
    c.add_item('apple', 1.0, 2)
    assert c.items() == {'apple': 5}

    with pytest.raises(ValueError):
        c.add_item('apple', 2.0)  # different unit price

    c.remove_item('apple', 4)
    assert c.items() == {'apple': 1}
    c.remove_item('apple')  # default quantity 1 removes it
    assert c.items() == {}

    with pytest.raises(KeyError):
        c.remove_item('banana')

# ------------------- subtotal and bulk discounts in cart -------------------

def test_cart_subtotal_bulk_discounts():
    c = cart.Cart()
    # 12 apples at $10 each => bulk discount 5%
    c.add_item('apple', 10.0, 12)
    expected_before = 12 * 10.0
    expected_after = expected_before * (1 - 0.05)  # 5% off
    assert c.subtotal() == round(expected_after, 2)

    # add 60 bananas at $1 each => bulk discount 10%
    c.add_item('banana', 1.0, 60)
    subtotal_apple = expected_after
    banana_before = 60 * 1.0
    banana_after = banana_before * (1 - 0.10)
    total_expected = round(subtotal_apple + banana_after, 2)
    assert c.subtotal() == total_expected

# ------------------- total calculation with coupon and shipping -------------------

def test_cart_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item('widget', 100.0, 10)  # bulk discount 5% -> subtotal 950
    # subtotal: 10*100=1000, minus 5% = 950
    assert c.subtotal() == 950.0
    # apply SAVE20 coupon => reduce by 20%
    after_coupon = 950.0 * (1 - 0.20)
    # shipping for subtotal after coupon: after_coupon < 1000 -> fee 60
    expected_total = round(after_coupon + 60, 2)
    assert c.total(coupon='SAVE20') == expected_total

def test_cart_total_no_shipping_for_free():
    c = cart.Cart()
    # 15 units at $10 each => bulk 5% -> subtotal 142.5
    c.add_item('item', 10.0, 15)
    subtotal = round(15 * 10.0 * (1 - 0.05), 2)  # 142.5
    assert c.subtotal() == subtotal
    # add coupon to bring below free threshold but shipping only applies if after coupon < 1000
    total = c.total(coupon='SAVE1')
    # subtotal after coupon: 142.5 * .99 = 141.225 -> round 141.23? Actually rounding step is after adding shipping, so compute exact
    amount_after_coupon = 142.5 * (1 - 0.01)
    shipping = cart.shipping_fee(amount_after_coupon)
    expected = round(amount_after_coupon + shipping, 2)
    assert total == expected

# Empty cart should not charge shipping

def test_empty_cart_no_shipping():
    c = cart.Cart()
    assert c.total() == 0.0
