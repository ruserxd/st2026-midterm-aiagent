import pytest
import cart

# --- apply_discount tests ---

@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),            # example from spec
        (100, 0, 100.0),             # no discount
        (50, 100, 0.0),              # full discount
        (99.99, 33, 66.99),          # computed: round(99.99*(1-0.33),2)
    ],
)
def test_apply_discount(price, percent, expected):
    result = cart.apply_discount(price, percent)
    assert isinstance(result, float)
    assert result == pytest.approx(expected)

@pytest.mark.parametrize(
    "price,percent",
    [
        (-10, 20),   # negative price
        (100, -5),   # negative percent
        (100, 105),  # percent >100
        (-5, -10),   # both invalid
    ],
)
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --- bulk_discount_percent tests ---

@pytest.mark.parametrize(
    "quantity,expected",
    [
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
    result = cart.bulk_discount_percent(quantity)
    assert result == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -5, 3.5],
)
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --- parse_coupon tests ---

valid_codes = [
    ("SAVE10", 10),
    ("save20", 20),
    ("   SAVE50  ", 50),
    ("Save1", 1),
    ("SAVE5", 5),
]

@pytest.mark.parametrize(
    "code,expected",
    valid_codes,
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

invalid_codes = [
    "SAV10",       # missing 'E'
    "SAVE0",        # below 1
    "SAVE51",       # above 50
    "12345",        # not matching pattern
    "SAVE-5",       # negative number
    "",             # empty string
    "  ",           # only whitespace
    "SAVE TEN",     # space inside number
]

@pytest.mark.parametrize(
    "code",
    invalid_codes,
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee tests ---

@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (1000, False, 0),
        (1200.00, True, 0),
        (999.99, False, 60),
        (500, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-1, -100],
)
def test_shipping_fee_negative_subtotal(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --- Cart tests ---

def test_cart_initial_state():
    c = cart.Cart()
    assert isinstance(c.items(), dict)
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

def test_add_item_and_subtotal():
    c = cart.Cart()
    c.add_item("apple", unit_price=100, quantity=5)
    assert c.items() == {"apple": 5}
    assert c.subtotal() == 500.0

    # Add same item with same price
    c.add_item("apple", unit_price=100, quantity=3)
    assert c.items() == {"apple": 8}
    assert c.subtotal() == 800.0

def test_add_item_errors():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("banana", unit_price=-10, quantity=2)

    with pytest.raises(ValueError):
        c.add_item("orange", unit_price=20, quantity=0)  # non‑positive quantity

    c.add_item("pear", unit_price=30, quantity=1)
    with pytest.raises(ValueError):
        c.add_item("pear", unit_price=25, quantity=2)  # price mismatch

def test_remove_item_and_items():
    c = cart.Cart()
    c.add_item("mango", unit_price=50, quantity=4)

    # Remove part of the quantity
    c.remove_item("mango", quantity=2)
    assert c.items() == {"mango": 2}
    assert c.subtotal() == 100.0

    # Remove remaining (or more) quantity; item should be gone
    c.remove_item("mango", quantity=5)
    assert c.items() == {}
    assert c.subtotal() == 0

    # Removing a non‑existent item raises KeyError
    with pytest.raises(KeyError):
        c.remove_item("kiwi", quantity=1)

def test_total_without_coupon_and_member():
    c = cart.Cart()
    c.add_item("item1", unit_price=200, quantity=3)  # subtotal 600

    total_non_member = c.total(member=False)
    assert total_non_member == pytest.approx(660.0)  # 600 + 60 shipping

    total_member = c.total(member=True)
    assert total_member == pytest.approx(630.0)  # 600 + 30 shipping

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("bulk", unit_price=300, quantity=5)   # subtotal 1500

    # Coupon that keeps amount >=1000 => free shipping
    total_with_free_ship = c.total(member=False, coupon="SAVE10")  # 1500 * 0.90 = 1350, free shipping
    assert total_with_free_ship == pytest.approx(1350.0)

    c2 = cart.Cart()
    c2.add_item("bulk", unit_price=200, quantity=5)   # subtotal 1000
    total_with_shipping = c2.total(member=False, coupon="SAVE10")  # 1000 * 0.90 + 60 shipping = 960
    assert total_with_shipping == pytest.approx(960.0)

def test_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("item", unit_price=100, quantity=1)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")

# Test that Cart.total rounds to 2 decimals

def test_cart_total_rounding():
    c = cart.Cart()
    # Use prices that create many decimal places
    c.add_item("precise", unit_price=123.456, quantity=1)
    total = c.total(member=False)  # 123.456 + 60 shipping = 183.456 -> round to 183.46
    assert total == pytest.approx(183.46)
