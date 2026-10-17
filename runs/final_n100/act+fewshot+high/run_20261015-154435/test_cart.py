import pytest
import cart

# Helper functions for manual calculations used in tests
def bulk_discount(qty):
    if qty >= 100:
        return 15
    elif qty >= 50:
        return 10
    elif qty >= 10:
        return 5
    else:
        return 0

def discount(amount, percent):
    """Return amount reduced by percent, rounded to two decimals."""
    return round(amount * (1 - percent / 100), 2)

def shipping(subtotal, member=False):
    if subtotal >= 1000:
        return 0
    return 30 if member else 60

def parse_coupon_code(code):
    cleaned = code.strip().lower()
    if not cleaned.startswith('save'):
        raise ValueError("Invalid coupon format")
    num_part = cleaned[4:]
    if not num_part.isdigit():
        raise ValueError("Coupon number must be digits")
    percent = int(num_part)
    if not (1 <= percent <= 50):
        raise ValueError("Coupon percent out of range")
    return percent

# ---------- apply_discount ----------
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200.0, 15, 170.0),
        (100.0, 0, 100.0),
        (50.0, 100, 0.0),
        (99.99, 10, 89.99),  # 99.99*0.9=89.991 -> rounded to 2 decimals
    ],
)
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize(
    "price,percent",
    [
        (-10, 20),
        (50, -5),
        (50, 105),
    ],
)
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (1, 0),
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -1, 2.5, "a"],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises((ValueError, TypeError)):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20 ", 20),
        ("  SaVe30", 30),
        ("SAVE05", 5),   # leading zeros
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "SAVE0",
        "SAVE51",
        "SAVEXX",
        "HELLO",
        "",
        "SAVE",  # missing number
        " s a v e10 ",  # malformed
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (1000.0, False, 0),
        (999.99, False, 60),
        (2000.5, True, 0),
        (800, True, 30),
        (500, False, 60),
        (500, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-1, -100],
)
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart ----------
def test_cart_initial_state():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

@pytest.mark.parametrize(
    "unit_price,quantity",
    [
        (10, 2.5),
        (10, 'a'),
    ],
)
def test_add_item_invalid_quantity_type(unit_price, quantity):
    c = cart.Cart()
    with pytest.raises((ValueError, TypeError)):
        c.add_item('item', unit_price, quantity=quantity)

@pytest.mark.parametrize(
    "unit_price,quantity",
    [
        (10, 0),
        (10, -1),
    ],
)
def test_add_item_invalid_quantity(unit_price, quantity):
    c = cart.Cart()
    with pytest.raises((ValueError, TypeError)):
        c.add_item('item', unit_price, quantity=quantity)

@pytest.mark.parametrize(
    "unit_price,quantity",
    [
        (-5, 1),      # negative unit price
    ],
)
def test_add_item_invalid_unit_price(unit_price, quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item('item', unit_price, quantity=quantity)

def test_add_item_default_quantity():
    c = cart.Cart()
    c.add_item('default_qty', 5)
    assert c.items() == {'default_qty': 1}
    assert c.subtotal() == 5.0

def test_add_and_items_integration():
    c = cart.Cart()
    c.add_item('apple', 100, quantity=2)
    assert c.items() == {'apple': 2}
    # no bulk discount
    assert c.subtotal() == 200.0

    # add same item again with same price
    c.add_item('apple', 100, quantity=3)
    assert c.items() == {'apple': 5}
    assert c.subtotal() == 500.0

    # mismatched price raises ValueError
    with pytest.raises(ValueError):
        c.add_item('apple', 120)

def test_remove_item_basic():
    c = cart.Cart()
    c.add_item('orange', 10, quantity=4)
    c.remove_item('orange', 2)
    assert c.items() == {'orange': 2}
    assert c.subtotal() == 20.0

    # removing more than remaining removes item completely
    c.remove_item('orange', 5)
    assert c.items() == {}
    assert c.subtotal() == 0

def test_remove_nonexistent_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item('pear', 1)

def test_items_is_copy():
    c = cart.Cart()
    c.add_item('grape', 5, quantity=3)
    d = c.items()
    d['grape'] = 10
    assert c.items() == {'grape': 3}

# Subtotal calculation with bulk discounts
def test_cart_subtotal_with_bulk_discounts():
    c = cart.Cart()
    unit_price1 = 99.99
    qty1 = 50   # triggers 10% discount
    c.add_item('item1', unit_price1, quantity=qty1)

    unit_price2 = 30
    qty2 = 5    # no bulk discount
    c.add_item('item2', unit_price2, quantity=qty2)

    def discounted_line(unit_price, qty):
        percent = bulk_discount(qty)
        line_total = unit_price * qty
        return round(line_total * (1 - percent / 100), 2)

    expected_subtotal = round(
        discounted_line(unit_price1, qty1) + discounted_line(unit_price2, qty2),
        2,
    )
    assert c.subtotal() == expected_subtotal

# Total calculations
def test_cart_total_no_coupon():
    c = cart.Cart()
    unit_price = 100
    qty = 9  # no bulk discount
    c.add_item('bulk_no_disc', unit_price, quantity=qty)

    def discounted_line(unit_price, qty):
        percent = bulk_discount(qty)
        return round(unit_price * qty * (1 - percent / 100), 2)

    subtotal_before_coupon = round(discounted_line(unit_price, qty), 2)
    amount_after_coupon = subtotal_before_coupon
    shipping_fee_value = shipping(amount_after_coupon)
    expected_total = round(amount_after_coupon + shipping_fee_value, 2)

    assert c.total() == expected_total

def test_cart_total_with_coupon_and_member():
    c = cart.Cart()
    unit_price = 100
    qty = 9
    c.add_item('bulk_no_disc', unit_price, quantity=qty)

    def discounted_line(unit_price, qty):
        percent = bulk_discount(qty)
        return round(unit_price * qty * (1 - percent / 100), 2)

    subtotal_before_coupon = round(discounted_line(unit_price, qty), 2)
    coupon_percent_value = parse_coupon_code('SAVE10')
    amount_after_coupon = discount(subtotal_before_coupon, coupon_percent_value)
    shipping_fee_val = shipping(amount_after_coupon, member=True)
    expected_total = round(amount_after_coupon + shipping_fee_val, 2)

    assert c.total(member=True, coupon='SAVE10') == expected_total

def test_cart_total_coupon_shrinks_shipping():
    c = cart.Cart()
    unit_price = 200
    qty = 6   # subtotal 1200, no bulk discount
    c.add_item('expensive', unit_price, quantity=qty)

    def discounted_line(unit_price, qty):
        percent = bulk_discount(qty)
        return round(unit_price * qty * (1 - percent / 100), 2)

    subtotal_before_coupon = round(discounted_line(unit_price, qty), 2)
    coupon_percent_value = parse_coupon_code('SAVE20')
    amount_after_coupon = discount(subtotal_before_coupon, coupon_percent_value)
    shipping_fee_val = shipping(amount_after_coupon)  # member default False
    expected_total = round(amount_after_coupon + shipping_fee_val, 2)

    assert c.total(coupon='SAVE20') == expected_total

def test_cart_total_free_shipping():
    c = cart.Cart()
    unit_price = 200
    qty = 6   # subtotal 1200, no bulk discount
    c.add_item('expensive', unit_price, quantity=qty)

    assert c.total() == 1200.0
    assert c.total(member=True) == 1200.0

def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0
    assert c.total(member=True) == 0
    with pytest.raises(ValueError):
        c.total(coupon='BADCODE')

def test_cart_total_invalid_coupon_nonempty():
    c = cart.Cart()
    c.add_item('item', 10, quantity=1)
    with pytest.raises(ValueError):
        c.total(coupon='BAD')
