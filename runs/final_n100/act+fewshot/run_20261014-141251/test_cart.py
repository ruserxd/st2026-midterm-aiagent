import pytest
import cart

# --------------------------------------------------------------------------
# apply_discount
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount_normal(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# --------------------------------------------------------------------------
# bulk_discount_percent
@pytest.mark.parametrize("qty,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -5, 3.4])
def test_bulk_discount_percent_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# --------------------------------------------------------------------------
# parse_coupon
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    ("  SaVe5  ", 5),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVE0",
    "SAVE51",
    "NOTCODESO",
    "save-5",
    "",
    "  ",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --------------------------------------------------------------------------
# shipping_fee
@pytest.mark.parametrize("subtotal,expected", [
    (0, 60),
    (999.99, 60),
    (1000, 0),
    (1500, 0),
])
def test_shipping_fee_non_member(subtotal, expected):
    assert cart.shipping_fee(subtotal) == expected

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

@pytest.mark.parametrize("subtotal,expected", [
    (0, 30),
    (500, 30),
    (1000, 0),
])
def test_shipping_fee_member(subtotal, expected):
    assert cart.shipping_fee(subtotal, member=True) == expected

# --------------------------------------------------------------------------
# Cart class
@pytest.fixture
def empty_cart():
    return cart.Cart()

def test_cart_initially_empty(empty_cart):
    assert empty_cart.items() == []
    assert empty_cart.subtotal() == 0.0
    assert empty_cart.total() == 0.0

def test_add_item_updates_subtotal_and_items(empty_cart):
    empty_cart.add_item("apple", unit_price=100, quantity=3)
    empty_cart.add_item("banana", unit_price=50)
    assert empty_cart.subtotal() == 350.0
    assert empty_cart.items() == [
        ("apple", 100, 3),
        ("banana", 50, 1),
    ]

def test_remove_item_decrements_or_removes(empty_cart):
    empty_cart.add_item("orange", unit_price=200, quantity=5)
    empty_cart.remove_item("orange", quantity=2)
    assert any(name == "orange" and qty == 3 for name, _, qty in empty_cart.items())
    empty_cart.remove_item("orange", quantity=3)
    assert all(name != "orange" for name, _, _ in empty_cart.items())
    with pytest.raises(ValueError):
        empty_cart.remove_item("orange")

def test_total_with_coupon_and_shipping(empty_cart):
    empty_cart.add_item("item", unit_price=400, quantity=3)  # subtotal 1200
    assert empty_cart.total(coupon="SAVE10") == 1080.00
    empty_cart.remove_item("item", quantity=3)
    empty_cart.add_item("small", unit_price=200, quantity=1)
    assert empty_cart.total(member=True) == 230.00

def test_total_invalid_coupon(empty_cart):
    empty_cart.add_item("test", unit_price=100)
    with pytest.raises(ValueError):
        empty_cart.total(coupon="BADCODE")
