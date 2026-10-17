import pytest
import cart

# ---------------------------------------------------------------------------
# Helpers for building carts in a readable way.
# ---------------------------------------------------------------------------

def make_cart(**items):
    """Return a Cart with the given items added.
    ``items`` is mapping name -> (unit_price, quantity).
    For convenience you can pass just unit price and quantity
    as a tuple or a single number (quantity defaults to 1)."""
    c = cart.Cart()
    for name, spec in items.items():
        if isinstance(spec, (tuple, list)):
            unit_price, qty = spec
        else:
            unit_price, qty = spec, 1
        c.add_item(name, unit_price, qty)
    return c

# ---------------------------------------------------------------------------
# Tests for the standalone helper functions.
# ---------------------------------------------------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200.0, 15) == 170.0

@ pytest.mark.parametrize(
    "price, percent, expected",
    [
        (100.0, 0, 100.0),
        (123.45, 50, 61.72),  # 123.45 * .5 = 61.725 rounded to 2 decimals
        (99.999, 1, 98.99901)  # 1% discount; round to 2 decimals -> 98.99901≈98.99?  actually round
    ],
)
def test_apply_discount_rounding(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@ pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [-5, 110])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# bulk_discount_percent -------------------------------------------------------

def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("quantity", [0, -3, 2.5])
def test_bulk_discount_invalid_quantity_raises(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(int(quantity)) if isinstance(quantity, int) else cart.bulk_discount_percent(quantity)

# parse_coupon ---------------------------------------------------------------

def test_parse_coupon_basic():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon(" save20 ") == 20
    assert cart.parse_coupon("SaVe5") == 5

@ pytest.mark.parametrize("code", ["",
                                   "SAVEBAD",
                                   "12345",
                                   "SAVE0",
                                   "SAVE51",
                                   " SAVE-1 ",
                                   "SAVEXX"])
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee ---------------------------------------------------------------

def test_shipping_fee():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(1500, member=True) == 0

@ pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_negative_subtotal_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------------------------------------------------------------------------
# Cart class tests.
# ---------------------------------------------------------------------------

def test_cart_initially_empty():
    c = cart.Cart()
    assert list(c.items().keys()) == []
    assert c.subtotal() == 0.0
    assert c.total() == 0.0

def test_add_and_items_basic():
    c = make_cart(A="10", B=(5, 2))
    assert c.items() == {"A":1, "B":2}

@ pytest.mark.parametrize("name, unit_price, qty", [
    ("X", -5, 1),
    ("Y", 5, 0),
    ("Z", 3, -2),
])
def test_add_item_invalid(name, unit_price, qty):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item(name, unit_price, qty)

@ pytest.mark.parametrize("name, existing_unit, new_unit", [(
    "A", 10.0, 12.0),
])
def test_add_item_different_price_raises(name, existing_unit, new_unit):
    c = cart.Cart()
    c.add_item(name, existing_unit)
    with pytest.raises(ValueError):
        c.add_item(name, new_unit)

# bulk discount effect on subtotal ------------------------------------------

def test_subtotal_with_bulk_discount():
    # 10 items at $1 each → bulk discount of 5% per item.
    c = make_cart(Widget=(1.0, 10))
    expected_per_item = 1.0 * (1 - cart.bulk_discount_percent(10) / 100)
    assert c.subtotal() == round(10 * expected_per_item, 2)

# total calculations --------------------------------------------------------

def test_total_no_coupon_and_non_member():
    c = make_cart(Item=(50.0, 1))  # subtotal $50 → shipping 60
    assert c.total() == round(50 + 60, 2)  # 110

def test_total_with_coupon_and_member():
    c = make_cart(Product=(200.0, 1))  # subtotal 200 → shipping 60, member 30
    coupon_percent = cart.parse_coupon("SAVE10")
    amount_after_coupon = 200 * (1 - coupon_percent / 100)
    shipping = cart.shipping_fee(amount_after_coupon, member=True)
    expected_total = round(amount_after_coupon + shipping, 2)
    assert c.total(member=True, coupon="SAVE10") == expected_total

# error paths ---------------------------------------------------------------

def test_remove_nonexistent_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("doesnotexist")

@ pytest.mark.parametrize("name", ["A", "B"])
def test_remove_to_zero_removes(name):
    c = make_cart(A=(5, 3))
    c.remove_item("A", 2)  # left 1
    assert c.items() == {"A":1}
    c.remove_item("A")   # remove last -> should be removed
    assert "A" not in c.items()

# coupon error handling ------------------------------------------------------

def test_total_invalid_coupon_raises():
    c = make_cart(Item=(10.0, 1))
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# ---------------------------------------------------------------------------
# End of tests.
# ---------------------------------------------------------------------------
