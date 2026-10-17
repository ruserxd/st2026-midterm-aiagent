import pytest
import cart

# Utility to create a cart with some items for reuse

def make_cart(items):
    c = cart.Cart()
    for name, price, qty in items:
        c.add_item(name, price, qty)
    return c

# ----- apply_discount -----
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),   # example from spec
        (100, 0, 100.0),     # no discount
        (50, 100, 0.0),      # full discount
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price", [ -1, -0.01])
def test_apply_discount_price_negative(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_percent_out_of_bounds(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ----- bulk_discount_percent -----
@pytest.mark.parametrize(
    "quantity,expected",
    [ (9, 0), (10, 5), (49, 5), (50, 10), (99, 10), (100, 15), (150, 15) ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ----- parse_coupon -----
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        ("   SaVe5  ", 5),
        ("SaVe50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "", "SAVE", "SAVExx", "SAVEBIG", "save0", "save51", "  foo  ", "12" , None,
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ----- shipping_fee -----
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [ (999.99, False, 60), (1000, False, 0), (1200, True, 0), (800, True, 30), ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -0.01])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ----- Cart class -----
@pytest.fixture
def empty_cart():
    return cart.Cart()

def test_add_item_new(empty_cart):
    empty_cart.add_item("apple", 1.0, 3)
    assert empty_cart.items() == {"apple": 3}

def test_add_item_increase_quantity(empty_cart):
    empty_cart.add_item("apple", 1.0, 2)
    empty_cart.add_item("apple", 1.0, 4)
    assert empty_cart.items() == {"apple": 6}

def test_add_item_price_mismatch(empty_cart):
    empty_cart.add_item("banana", 0.5, 1)
    with pytest.raises(ValueError):
        empty_cart.add_item("banana", 0.75, 2)

@pytest.mark.parametrize("unit_price,qty", [(-1, 1), (1, 0), (1, -2)])
def test_add_item_invalid(unit_price, qty):
    with pytest.raises(ValueError):
        empty_cart.add_item("pear", unit_price, qty)

def test_remove_item_decrease(empty_cart):
    empty_cart.add_item("orange", 0.8, 5)
    empty_cart.remove_item("orange", 2)
    assert empty_cart.items() == {"orange": 3}

def test_remove_item_zero_removal(empty_cart):
    empty_cart.add_item("grape", 0.3, 4)
    empty_cart.remove_item("grape", 4)
    assert empty_cart.items() == {}

def test_remove_nonexistent_key(empty_cart):
    with pytest.raises(KeyError):
        empty_cart.remove_item("plum", 1)

# ----- subtotal -----
@pytest.mark.parametrize(
    "items,expected",
    [
        ([], 0.00),
        ([("a", 10, 5)], 10*5 * (1-0.05)),  # quantity 5 => 5% discount
        ([("b", 20, 12)], 20*12*(1-0.05)),   # 12 => 5%
        ([("c", 30, 55)], 30*55*(1-0.10)),   # 55 => 10%
        ([("d", 40, 110)], 40*110*(1-0.15)),# 110 => 15%
    ],
)
def test_subtotal(items, expected):
    c = make_cart([(name,p,qty) for name,p,qty in items])
    # round to two decimals as spec says
    assert round(c.subtotal(), 2) == round(expected, 2)

# ----- total with coupon and shipping -----
def test_total_basic(empty_cart):
    empty_cart.add_item("x", 100, 1)
    assert empty_cart.total() == 160.0  # subtotal 100 + shipping 60

def test_total_coupon_and_shipping(empty_cart):
    empty_cart.add_item("y", 200, 2)  # subtotal 400
    total = empty_cart.total(coupon="SAVE10")
    # after coupon: 360, shipping 60 -> 420
    assert total == 420.0

def test_total_invalid_coupon(empty_cart):
    empty_cart.add_item("z", 50, 1)
    with pytest.raises(ValueError):
        empty_cart.total(coupon="BAD")

# ----- empty cart cost -----
def test_empty_cart_total_zero(empty_cart):
    assert empty_cart.total() == 0.0
