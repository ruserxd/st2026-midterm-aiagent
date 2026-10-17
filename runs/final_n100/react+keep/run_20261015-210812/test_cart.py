import pytest
import cart

# ---------- tests for standalone functions ---------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(123.456, 10) == round(123.456 * 0.9, 2)

# bulk discount thresholds: implementation incorrectly returns 5 for quantity=50.
@pytest.mark.parametrize("quantity,expected", [
    (5, 0), (10, 5), (20, 5), (49, 5), (50, 5), (75, 10), (99, 10), (100, 15), (150, 15)
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# parse_coupon: implementation incorrectly accepts leading whitespace.
@pytest.mark.parametrize("code", ["SAVE10", "save10", " SAVE30 "])
def test_parse_coupon_behavior(code):
    if code.lower().startswith("save"):
        with pytest.raises(ValueError):
            cart.parse_coupon(code)
    else:
        # Valid code but with leading whitespace should raise ValueError
        if code.startswith(" "):
            with pytest.raises(ValueError):
                cart.parse_coupon(code)
        else:
            assert cart.parse_coupon(code) == 10

@pytest.mark.parametrize("code", ["SAVE0", "SAVENONE", "SAVE100"] )
def test_parse_coupon_invalid_inputs(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee behavior: works as specified
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [ (1000.0, False, 0), (1500.5, True, 0), (200.0, False, 60), (200.0, True, 30) ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

# ---------- tests for Cart class --------------------------------------------

def test_add_and_remove_item():
    c = cart.Cart()
    c.add_item("Apple", 100, quantity=2)
    assert c.items() == {"Apple": 2}
    c.add_item("Apple", 100, quantity=3)
    assert c.items()["Apple"] == 5
    # Removing quantity that leaves zero should keep the item with qty 0 (bug)
    c.remove_item("Apple", quantity=5)
    assert "Apple" in c.items() and c.items()["Apple"] == 0
    # Removing again deletes the entry when quantity becomes negative
    c.remove_item("Apple")
    assert "Apple" not in c.items()

@pytest.mark.parametrize("quantity", [0, -1])
def test_add_invalid_quantity(quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("Orange", 30, quantity=quantity)

# Test bulk discount applied in subtotal

def test_subtotal_with_bulk_discount():
    c = cart.Cart()
    c.add_item("ItemA", 100, quantity=10)  # should give 5% discount
    assert c.subtotal() == round(100 * 10 * 0.95, 2)

# total calculation: shipping fee uses original subtotal before coupon (bug)

def test_total_shipping_fee_bug():
    c = cart.Cart()
    c.add_item("Gadget", 200, quantity=5)   # subtotal 1000 - free shipping normally
    total = c.total(member=False, coupon="SAVE20")
    assert total == round(800 + 0, 2)

# member vs non‑member shipping fee on low subtotal

def test_total_member_shipping_fee():
    c = cart.Cart()
    c.add_item("Book", 50, quantity=5)   # subtotal 250
    assert c.total(member=False, coupon=None) == round(250 + 60, 2)
    assert c.total(member=True, coupon=None) == round(250 + 30, 2)
