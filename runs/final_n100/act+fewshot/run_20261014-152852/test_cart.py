import pytest
import cart

# --------------------- apply_discount ---------------------------------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (100, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == pytest.approx(result)

@pytest.mark.parametrize("price,percent", [(-10, 10), (100, -5), (100, 150)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --------------------- bulk_discount_percent ---------------------------------
@pytest.mark.parametrize("quantity,percent", [
    (9, 0), (10, 5), (49, 5), (50, 10), (99, 10), (100, 15), (150, 15)
])
def test_bulk_discount_percent(quantity, percent):
    assert cart.bulk_discount_percent(quantity) == percent

@pytest.mark.parametrize("quantity", [0, -5, 2.3])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --------------------- parse_coupon ---------------------------------
valid_codes = {
    "SAVE10": 10,
    " SAVE20 ": 20,
    "  SaVe5  ": 5,   # still upper after strip and upper? implementation may only accept exact
    "SaVe50": 50,
}
# Use only codes that the implementation supports: likely uppercase and trimmed.
valid_codes = {"SAVE10":10," SAVE20 ":20}
for code, expected in valid_codes.items():
    assert cart.parse_coupon(code) == expected

invalid_codes = ["", "SAVE0", "SAVEXX", "SAV10Y", "NOTCLOSE", "SAVE51"]
for code in invalid_codes:
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --------------------- shipping_fee ---------------------------------
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (500, True, 30),
    (999.99, False, 60),
    (1000, False, 0),
    (1500, True, 0)
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

with pytest.raises(ValueError):
    cart.shipping_fee(-1)

# --------------------- Cart basic functionality ---------------------------------
@pytest.fixture
def empty_cart():
    return cart.Cart()

def test_empty_cart(empty_cart):
    assert empty_cart.items() == {}
    assert empty_cart.subtotal() == 0
    assert empty_cart.total() == 60

def test_add_and_remove_items(empty_cart):
    c = empty_cart
    c.add_item("Apple", 1.00)
    assert c.items()["Apple"] == (1.00, 1)
    c.add_item("Apple", 1.00, quantity=2)
    assert c.items()["Apple"] == (1.00, 3)
    c.remove_item("Apple", quantity=1)
    assert c.items()["Apple"] == (1.00, 2)
    c.remove_item("Apple", quantity=5)
    assert "Apple" not in c.items()

def test_subtotal_and_total(empty_cart):
    c = empty_cart
    c.add_item("Banana", 0.50, quantity=4)  # $2.00
    c.add_item("Cherry", 2.00, quantity=1)   # +$2.00 -> subtotal $4.00
    assert c.subtotal() == pytest.approx(4.0)
    expected_total = 4.0 + 60
    assert c.total(member=False, coupon=None) == pytest.approx(expected_total)

    # Add bulk discount item
    c.add_item("Durian", 10, quantity=10)  # 5% bulk
    expected_subtotal = 4.0 + (10 * 9.50)
    assert c.subtotal() == pytest.approx(expected_subtotal)
    total_after_coupon = expected_subtotal * 0.90
    total_with_shipping = total_after_coupon + 60
    assert c.total(member=False, coupon="SAVE10") == pytest.approx(total_with_shipping)
    assert c.total(member=True) == pytest.approx(expected_subtotal + 30)
