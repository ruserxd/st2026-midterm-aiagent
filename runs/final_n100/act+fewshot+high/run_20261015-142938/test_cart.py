import pytest
import cart

# ---------- apply_discount tests ----------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(100, 100) == 0.0
    # Rounding with non-integer result
    assert cart.apply_discount(123.456, 10) == round(123.456 * 0.9, 2)

@ pytest.mark.parametrize("price", [-1, -50])
@ pytest.mark.parametrize("percent", [10, 20])
def test_apply_discount_negative_price(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

@ pytest.mark.parametrize("price", [100, 200])
@ pytest.mark.parametrize("percent", [-5, -1, 105, 150])
def test_apply_discount_invalid_percent(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent tests ----------

def test_bulk_discount_percent_bounds():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

def test_bulk_discount_percent_invalid():
    for qty in [0, -1, -50]:
        with pytest.raises(ValueError):
            cart.bulk_discount_percent(qty)

# ---------- parse_coupon tests ----------

def test_parse_coupon_valid_cases():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon(" SAVE30 ") == 30

@ pytest.mark.parametrize("code", ["",
                                   "SAVE0",
                                   "SAVE51",
                                   "sve10",
                                   "SAVEabc",
                                   "SAVE-5",
                                   " SAVE10x ",
                                   "   SAVE   "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee tests ----------

def test_shipping_fee_non_member():
    assert cart.shipping_fee(1001) == 0
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(999) == 60
    assert cart.shipping_fee(0) == 60

@ pytest.mark.parametrize("subtotal,member",[(999,True),(500,True),(0,True)])
def test_shipping_fee_member(subtotal, member):
    # Member pays half of the fee (30)
    if subtotal >= 1000:
        assert cart.shipping_fee(subtotal, member) == 0
    else:
        assert cart.shipping_fee(subtotal, member) == 30

@ pytest.mark.parametrize("subtotal",[-1,-10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart tests ----------

def test_cart_initial_state():
    c = cart.Cart()
    assert isinstance(c.items(), dict)
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 0.0


def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item("Apple", 100.0, 5)
    assert c.items() == {"Apple": 5}
    # Adding same item with same price increases quantity
    c.add_item("Apple", 100.0, 3)
    assert c.items() == {"Apple": 8}
    # Different price for existing item should raise ValueError
    with pytest.raises(ValueError):
        c.add_item("Apple", 120.0, 1)
    # Invalid unit_price and quantity
    with pytest.raises(ValueError):
        c.add_item("Banana", -10.0, 2)
    with pytest.raises(ValueError):
        c.add_item("Banana", 20.0, 0)


def test_cart_remove_item():
    c = cart.Cart()
    c.add_item("Apple", 100.0, 5)
    # Remove some quantity
    c.remove_item("Apple", 2)
    assert c.items() == {"Apple": 3}
    # Removing all remaining removes the item entirely
    c.remove_item("Apple", 3)
    assert c.items() == {}
    # Removing non-existent item raises KeyError
    with pytest.raises(KeyError):
        c.remove_item("Banana", 1)


def test_cart_subtotal_basic():
    c = cart.Cart()
    # Item A: price 100, qty 10 -> bulk discount 5%
    c.add_item("A", 100.0, 10)
    # Item B: price 50, qty 20 -> bulk discount 10%
    c.add_item("B", 50.0, 20)
    subtotal = round(100.0 * 10 * (1 - cart.bulk_discount_percent(10)/100), 2) +\
                round(50.0 * 20 * (1 - cart.bulk_discount_percent(20)/100), 2)
    assert c.subtotal() == subtotal


def test_cart_subtotal_decimal_rounding():
    c = cart.Cart()
    # Item with decimal price and qty triggering rounding
    c.add_item("C", 99.99, 11)  # bulk discount 5%
    expected_total = round(99.99 * 11 * (1 - cart.bulk_discount_percent(11)/100), 2)
    assert c.subtotal() == expected_total


def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0.0

# Helper to compute expected total based on spec logic

def expected_total(subtotal, coupon_percent=None, member=False):
    amount = subtotal
    if coupon_percent is not None:
        amount = round(amount * (1 - coupon_percent / 100), 2)
    fee = cart.shipping_fee(amount, member) if amount > 0 else 0
    return round(amount + fee, 2)


def test_cart_total_no_coupon_non_member():
    c = cart.Cart()
    c.add_item("X", 200.0, 6)  # qty 6 => no bulk discount
    subtotal = 200.0 * 6  # 1200
    assert c.total() == expected_total(subtotal)


def test_cart_total_no_coupon_member():
    c = cart.Cart()
    c.add_item("X", 20.0, 10)  # qty 10 => bulk discount 5%
    subtotal = round(20.0 * 10 * (1 - cart.bulk_discount_percent(10)/100), 2)
    assert c.total(member=True) == expected_total(subtotal, member=True)


def test_cart_total_with_coupon_non_member():
    c = cart.Cart()
    c.add_item("Y", 100.0, 5)  # qty <10 -> no bulk discount
    subtotal = 500.0
    assert c.total(coupon="SAVE10") == expected_total(subtotal, coupon_percent=10)


def test_cart_total_with_coupon_member():
    c = cart.Cart()
    c.add_item("Y", 100.0, 5)
    subtotal = 500.0
    assert c.total(coupon="SAVE20", member=True) == expected_total(subtotal, coupon_percent=20, member=True)


def test_cart_total_coupon_affects_shipping():
    # Subtotal >= 1000 without coupon, free shipping
    c = cart.Cart()
    c.add_item("Z", 200.0, 6)  # subtotal 1200
    assert c.total() == expected_total(1200)
    # Apply coupon to bring amount below 1000, shipping applies now
    assert c.total(coupon="SAVE10") == expected_total(1200, coupon_percent=10)


def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("A", 50.0, 5)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")

# End of tests
