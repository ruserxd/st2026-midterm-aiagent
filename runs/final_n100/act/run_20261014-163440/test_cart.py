import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# ---------- apply_discount tests ----------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@pytest.mark.parametrize(
    "price,percent",
    [
        (100, 0),     # no discount
        (50, 100),    # full discount to zero
    ],
)
def test_apply_discount_edge_cases(price, percent):
    expected = round(price * (1 - percent / 100.0), 2)
    assert apply_discount(price, percent) == expected

@pytest.mark.parametrize("price", [-10, -0.01])
def test_apply_discount_invalid_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 20)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- bulk_discount_percent tests ----------

def test_bulk_discount_basic():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@pytest.mark.parametrize("quantity", [0, -1])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon tests ----------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save25 ") == 25
    assert parse_coupon("  SaVe50") == 50
    # case-insensitivity
    assert parse_coupon("SaVe1") == 1

@pytest.mark.parametrize("code", ["", "SAVE0", "SAVE51", "DISCOUNT10", "SAVEX10", "SAVEx10", " SAVE10x "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee tests ----------

def test_shipping_fee_basic():
    assert shipping_fee(1200) == 0
    assert shipping_fee(1000) == 0
    assert shipping_fee(999.99) == 60
    # member discounts
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(1000, member=True) == 0

@pytest.mark.parametrize("subtotal", [-5, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart tests ----------

def test_cart_add_and_items():
    cart = Cart()
    cart.add_item('apple', 100, 2)
    cart.add_item('banana', 50)  # default quantity 1
    assert cart.items() == {
        'apple': (100, 2),
        'banana': (50, 1),
    }


def test_cart_remove():
    cart = Cart()
    cart.add_item('orange', 80, 3)
    cart.remove_item('orange')  # remove 1 by default
    assert cart.items() == {'orange': (80, 2)}
    cart.remove_item('orange', quantity=2)
    assert cart.items() == {}

@pytest.mark.parametrize("name", ['pear', 'mango'])
def test_cart_remove_nonexistent(name):
    cart = Cart()
    with pytest.raises(KeyError):
        cart.remove_item(name)


def test_cart_subtotal_and_total():
    cart = Cart()
    cart.add_item('pen', 120, 5)   # subtotal 600
    cart.add_item('paper', 300, 2) # subtotal + 600 = 1200
    assert cart.subtotal() == 1200
    # total without discount
    assert cart.total(member=False, coupon=None) == 1200 + shipping_fee(1200)
    # member should get half shipping
    assert cart.total(member=True, coupon=None) == 1200 + shipping_fee(1200, member=True)


def test_cart_total_with_coupon_and_bulk_discount():
    cart = Cart()
    # add 12 units of 'stapler' at $200 each - bulk discount applies (10%)
    cart.add_item('stapler', 200, 12)
    expected_subtotal = 2400
    assert cart.subtotal() == expected_subtotal
    bulk_percent = bulk_discount_percent(12)  # 5
    after_bulk = apply_discount(expected_subtotal, bulk_percent)
    coupon_percent = parse_coupon('SAVE20')
    final_no_shipping = apply_discount(after_bulk, coupon_percent)
    shipping = shipping_fee(final_no_shipping)
    total_expected = round(final_no_shipping + shipping, 2)
    assert cart.total(member=False, coupon='SAVE20') == total_expected

# Edge case: zero items

def test_cart_empty():
    cart = Cart()
    assert cart.subtotal() == 0
    assert cart.total() == shipping_fee(0)  # should be 60 for non-member
