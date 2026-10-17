import pytest
import cart

# Test apply_discount
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
        (123.45, 25, round(123.45 * 0.75, 2)),
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# Value errors for invalid price or percent
@pytest.mark.parametrize("price, percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# Test bulk_discount_percent
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (200, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 2.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# Test parse_coupon
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save25 ", 25),
        ("  SaVe50", 50),
        ("SAVE1", 1),
    ],
)
def test_parse_coupon(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["", "SAVExx", "save0", "save51", "  ", "123", "SAVE-5", "BAD10"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Test shipping_fee
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, 60),
        (999.99, False, 60),
        (1000, False, 0),
        (1500, True, 30),
        (200, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Test Cart class behavior
class DummyItem:
    def __init__(self, name, unit_price, quantity=1):
        self.name = name
        self.unit_price = unit_price
        self.quantity = quantity

@pytest.fixture
def sample_cart():
    c = cart.Cart()
    return c

# Adding items updates subtotal correctly

def test_add_item_updates_subtotal(sample_cart):
    c = sample_cart
    c.add_item("apple", 10, 2)
    c.add_item("banana", 5, 3)
    assert c.subtotal() == 10 * 2 + 5 * 3

# Removing items decreases quantity and subtotal; removes if zero

def test_remove_item(sample_cart):
    c = sample_cart
    c.add_item("apple", 10, 5)
    c.remove_item("apple", 2)
    assert any(it[1]['quantity'] == 3 for it in c.items())
    assert c.subtotal() == 10 * 3
    # Remove remaining 3 to delete item
    c.remove_item("apple", 3)
    assert not any(it[0] == "apple" for it in c.items())

# Total includes member discount and coupon

def test_total_with_member_and_coupon(sample_cart):
    c = sample_cart
    c.add_item("widget", 100, 10)  # quantity triggers bulk discount 5%
    total_before = c.subtotal()
    expected_discount = cart.apply_discount(total_before, 5)
    coupon_percent = cart.parse_coupon("SAVE20")
    after_coupon = cart.apply_discount(expected_discount, coupon_percent)
    shipping = cart.shipping_fee(after_coupon, member=True) if not isinstance(after_coupon, float) else after_coupon
    # As member, half shipping fee
    final_expected = after_coupon + (shipping/2)
    assert c.total(member=True, coupon="SAVE20") == pytest.approx(final_expected)

# Total without any discounts

def test_total_no_discounts(sample_cart):
    c = sample_cart
    c.add_item("item", 50, 1)
    assert c.total() == 50

# Total with invalid coupon raises ValueError

def test_total_invalid_coupon(sample_cart):
    c = sample_cart
    c.add_item("item", 20, 2)
    with pytest.raises(ValueError):
        c.total(coupon="BAD")

# items() returns list of tuples (name, details dict) with correct structure

def test_items_structure(sample_cart):
    c = sample_cart
    c.add_item("gizmo", 30, 4)
    items = c.items()
    assert len(items) == 1
    name, info = items[0]
    assert name == "gizmo"
    assert isinstance(info, dict)
    assert info["unit_price"] == 30
    assert info["quantity"] == 4

# Adding same item increases quantity

def test_add_same_item_increases_quantity(sample_cart):
    c = sample_cart
    c.add_item("dup", 10, 1)
    c.add_item("dup", 10, 3)
    assert any(it[0] == "dup" and it[1]["quantity"] == 4 for it in c.items())

# Removing more than existing quantity raises ValueError

def test_remove_more_than_exists(sample_cart):
    c = sample_cart
    c.add_item("excess", 5, 2)
    with pytest.raises(ValueError):
        c.remove_item("excess", 3)
