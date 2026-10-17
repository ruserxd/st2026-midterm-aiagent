import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount ----------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price,percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent ----------

def test_bulk_discount_limits():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@pytest.mark.parametrize("qty", [0, -1, 2.5])
def test_bulk_discount_errors(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)

# ---------- parse_coupon ----------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save10") == 10
    assert parse_coupon(" SAVE25 ") == 25

@pytest.mark.parametrize(
    "code",
    ["SAVExx", "SAVE0", "SAVE51", "foo", "SAVE-5"],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ----------

def test_shipping_fee_basic():
    assert shipping_fee(500) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(999.99) == 60

@pytest.mark.parametrize("member", [True, False])
def test_shipping_member_half(member):
    fee = shipping_fee(300, member=member)
    expected = 30 if member else 60
    assert fee == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_errors(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class ----------

def test_cart_add_and_items():
    cart = Cart()
    cart.add_item('apple', 100, quantity=3)
    cart.add_item('banana', 50)
    expected = {
        'apple': (100, 3),
        'banana': (50, 1),
    }
    assert cart.items() == expected

def test_cart_remove_and_subtotal():
    cart = Cart()
    cart.add_item('item', 200, quantity=5)
    cart.remove_item('item', quantity=2)
    assert cart.items()['item'] == (200, 3)
    assert cart.subtotal() == 600

def test_cart_total_with_member_and_coupon():
    cart = Cart()
    # No items: total should be shipping fee of 0 and subtotal 0
    assert cart.total(member=True) == 0.0

    # Add one expensive item > 1000 to trigger free shipping
    cart.add_item('widget', 1200)
    assert cart.total(member=False) == 1200.0

    # Bulk discount case
    cart.remove_item('widget')
    cart.add_item('small', 50, quantity=20)
    # bulk_discount_percent(20) -> 10%
    discounted_unit = apply_discount(50, 10)
    expected_subtotal = round(discounted_unit * 20, 2)
    total = cart.total(member=False)
    assert total == round(expected_subtotal + shipping_fee(expected_subtotal), 2)

def test_cart_total_with_coupon():
    cart = Cart()
    cart.add_item('toy', 200, quantity=2)
    subtotal = cart.subtotal()
    coupon_percent = parse_coupon("SAVE20")
    discount_amount = subtotal * (coupon_percent / 100)
    expected_subtotal_after_discount = round(subtotal - discount_amount, 2)
    total_expected = round(expected_subtotal_after_discount + shipping_fee(expected_subtotal_after_discount), 2)
    assert cart.total(coupon="save20") == total_expected
