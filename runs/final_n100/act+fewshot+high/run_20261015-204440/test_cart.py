import pytest
import cart

def round2(x):
    return round(float(x), 2)

# apply_discount tests
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
        (123.45, 33, round2(123.45 * 0.67)),
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price, percent",
    [(-10, 20), (50, -5), (50, 105)],
)
def test_apply_discount_invalid_parameters(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (250, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -1, 3.5],
)
def test_bulk_discount_percent_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save5", 5),
        (" SaVe50 ", 50),
        ("SAVE1", 1),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "",
        "   ",
        "SAVE0",
        "SAVE51",
        "SAVEB10",
        "SAVE10x",
        "SAVE-5",
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (999.99, False, 60),   # just below free threshold
        (1000, False, 0),      # exactly free
        (1500, False, 0),      # free regardless of membership
        (2000, True, 0),       # free regardless of membership
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-1, -100.5],
)
def test_shipping_fee_invalid_subtotal(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart class tests
@pytest.fixture
def empty_cart():
    return cart.Cart()

def test_empty_cart_properties(empty_cart):
    assert empty_cart.items() == {}
    assert empty_cart.subtotal() == 0
    assert empty_cart.total() == 0

def test_add_new_item(empty_cart):
    empty_cart.add_item("Apple", 1.5, quantity=3)
    assert empty_cart.items() == {"Apple": 3}
    assert empty_cart.subtotal() == round2(1.5 * 3)

def test_add_existing_item_increases_quantity(empty_cart):
    empty_cart.add_item("Banana", 0.8, quantity=4)
    empty_cart.add_item("Banana", 0.8, quantity=2)
    assert empty_cart.items() == {"Banana": 6}
    assert empty_cart.subtotal() == round2(0.8 * 6)

def test_add_item_price_mismatch(empty_cart):
    empty_cart.add_item("Orange", 1.2, quantity=2)
    with pytest.raises(ValueError):
        empty_cart.add_item("Orange", 1.3, quantity=1)

def test_add_item_invalid_parameters(empty_cart):
    with pytest.raises(ValueError):
        empty_cart.add_item("Mango", -1, quantity=2)   # negative price
    with pytest.raises(ValueError):
        empty_cart.add_item("Mango", 1, quantity=-3)   # non‑positive qty
    with pytest.raises(ValueError):
        empty_cart.add_item("Mango", 1, quantity=0)
    with pytest.raises(ValueError):
        empty_cart.add_item("Mango", 1.5, quantity=2.7)

def test_remove_partial_quantity(empty_cart):
    empty_cart.add_item("Grapes", 2.0, quantity=5)
    empty_cart.remove_item("Grapes", quantity=2)
    assert empty_cart.items() == {"Grapes": 3}

def test_remove_entire_quantity(empty_cart):
    empty_cart.add_item("Peach", 1.75, quantity=4)
    empty_cart.remove_item("Peach", quantity=5)   # more than existing
    assert empty_cart.items() == {}

def test_remove_nonexistent_item(empty_cart):
    with pytest.raises(KeyError):
        empty_cart.remove_item("Nonexistent", quantity=1)

def test_subtotal_with_bulk_discount():
    c = cart.Cart()
    c.add_item("ItemA", 10, quantity=5)
    c.add_item("ItemB", 20, quantity=12)   # qualifies for 5% discount
    expected = round2(10 * 5 + 20 * 12 * 0.95)
    assert c.subtotal() == expected

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("Thing", 100, quantity=3)   # subtotal 300
    total_no_member = c.total(coupon="SAVE10")
    assert total_no_member == round2(270 + 60)
    total_with_member = c.total(member=True, coupon="SAVE10")
    assert total_with_member == round2(270 + 30)

def test_total_free_shipping_after_coupon():
    c = cart.Cart()
    c.add_item("Expensive", 400, quantity=3)   # subtotal 1200
    total_no_member = c.total(coupon="SAVE10")  # 1080 >= 1000 -> free shipping
    assert total_no_member == round2(1080)

def test_total_invalid_coupon(empty_cart):
    with pytest.raises(ValueError):
        empty_cart.total(coupon="INVALID")

def test_total_empty_cart_no_shipping(empty_cart):
    assert empty_cart.total() == 0
