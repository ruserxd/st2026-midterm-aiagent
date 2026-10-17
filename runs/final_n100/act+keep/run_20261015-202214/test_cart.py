import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount tests ----------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (100, 0, 100.0),
        (50, 100, 0.0),
        (123.456, 10, 111.11),  # 123.456*0.9 = 111.1104 -> round to 2
    ],
)
def test_apply_discount_various(price, percent, expected):
    assert apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price, percent",
    [(-1, 10), (50, -5), (50, 105)],
)
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent tests ----------

def test_bulk_discount_brackets():
    assert bulk_discount_percent(5) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@pytest.mark.parametrize("quantity", [0, -3, 2.5])
def test_bulk_discount_errors(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon tests ----------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20 ") == 20
    assert parse_coupon("  SaVe5") == 5

@pytest.mark.parametrize(
    "code",
    ["SAVE0", "SAVE51", "SAVEXY", "DISCOUNT10", ""],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee tests ----------

def test_shipping_fee_basic():
    assert shipping_fee(1000) == 0
    assert shipping_fee(999.99) == 60
    assert shipping_fee(500, member=True) == 30

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart tests ----------

def test_cart_initial_empty():
    c = Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 0.0

def test_add_and_remove_items():
    c = Cart()
    c.add_item("Apple", 1.00, quantity=3)
    c.add_item("Banana", 0.50, quantity=2)
    assert c.items() == {"Apple": 3, "Banana": 2}
    # Adding same item increases quantity
    c.add_item("Apple", 1.00, quantity=2)
    assert c.items()["Apple"] == 5
    # Removing reduces quantity; remove more than present -> removal
    c.remove_item("Apple", quantity=3)
    assert c.items()["Apple"] == 2
    c.remove_item("Banana", quantity=2)
    assert "Banana" not in c.items()

def test_add_same_name_different_price_error():
    c = Cart()
    c.add_item("Milk", 1.20, quantity=1)
    with pytest.raises(ValueError):
        c.add_item("Milk", 1.30, quantity=1)

@pytest.mark.parametrize(
    "name, unit_price, quantity",
    [("Item", -5, 1), ("Item", 5, 0), ("Item", 5, -3)],
)
def test_add_item_invalid(name, unit_price, quantity):
    c = Cart()
    with pytest.raises(ValueError):
        c.add_item(name, unit_price, quantity)

@pytest.mark.parametrize(
    "name, quantity",
    [("NonExistent", 1), ("AlsoMissing", 5)],
)
def test_remove_nonexistent(name, quantity):
    c = Cart()
    with pytest.raises(KeyError):
        c.remove_item(name, quantity)

# ---------- subtotal calculations with bulk discount ----------

def test_subtotal_with_bulk_discount():
    c = Cart()
    # 10 units at $2.00 each -> bulk discount 5%
    c.add_item("Widget", 2.00, quantity=10)
    expected = round(2.0 * 10 * (1 - 0.05), 2)  # 19.0
    assert c.subtotal() == expected

# ---------- total calculation with coupon and shipping ----------

def test_total_with_coupon_and_shipping():
    c = Cart()
    c.add_item("Book", 30.00, quantity=1)
    subtotal = 30.0
    # Apply 10% coupon -> 27.0
    total_after_coupon = round(subtotal * (1 - 0.10), 2)
    shipping = shipping_fee(total_after_coupon)  # subtotal <1000 => 60
    expected_total = round(total_after_coupon + shipping, 2)
    assert c.total(coupon="SAVE10") == expected_total

# ---------- total with member discount on shipping ----------

def test_total_member_shipping_half():
    c = Cart()
    c.add_item("Expensive", 200.0, quantity=1)
    # subtotal 200 -> after no coupon still 200
    shipping = shipping_fee(200, member=True)  # 30
    expected_total = round(200 + shipping, 2)
    assert c.total(member=True) == expected_total

# ---------- total with empty cart (no shipping) ----------

def test_total_empty_cart_no_shipping():
    c = Cart()
    assert c.total() == 0.0
