import pytest
import cart

# ---------- Helper utilities ----------

def round_half_up(x):
    # helper used only in tests for expected values
    return round(x, 2)

# ---------- apply_discount tests ----------
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200.0, 15, 170.0),  # example from spec
        (100, 0, 100.0),
        (50.5, 20, round_half_up(40.4)),
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price, percent",
    [(-10, 10), (100, -5), (100, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent tests ----------
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (5, 0),
        (10, 5),
        (20, 5),
        (50, 10),
        (75, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 3.5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(int(quantity)) if isinstance(quantity, int) else cart.bulk_discount_percent(quantity)

# ---------- parse_coupon tests ----------
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        (" save20 ", 20),
        ("SaVe5", 5),
        ("save50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "ABC10", "SAVEXX", ""] )
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee tests ----------
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0.0, False, 60),
        (999.99, True, 30),
        (1000.0, False, 0),
        (1500.5, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart tests ----------

def test_cart_initially_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 0.0

# add_item: new item

def test_add_new_item_increases_quantity_and_price():
    c = cart.Cart()
    c.add_item("apple", unit_price=2.5, quantity=3)
    assert c.items() == {"apple": 3}
    # subtotal: no bulk discount yet (quantity <10)
    assert c.subtotal() == round_half_up(2.5 * 3)

# add_item: existing item same price

def test_add_existing_same_price_increases_quantity():
    c = cart.Cart()
    c.add_item("banana", unit_price=1.0, quantity=2)
    c.add_item("banana", unit_price=1.0, quantity=4)
    assert c.items() == {"banana": 6}
    # subtotal with bulk discount: 6<10 => no discount
    assert c.subtotal() == round_half_up(1.0 * 6)

# add_item: price mismatch raises

def test_add_existing_different_price_raises():
    c = cart.Cart()
    c.add_item("orange", unit_price=3.0, quantity=2)
    with pytest.raises(ValueError):
        c.add_item("orange", unit_price=4.0, quantity=1)

# add_item: invalid arguments

def test_add_item_invalid_arguments():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("pear", unit_price=-5, quantity=1)
    with pytest.raises(ValueError):
        c.add_item("pear", unit_price=3, quantity=0)

# remove_item: reduce quantity and delete when zero

def test_remove_item_decrease_and_delete():
    c = cart.Cart()
    c.add_item("grape", 0.5, quantity=4)
    c.remove_item("grape", quantity=2)
    assert c.items() == {"grape": 2}
    c.remove_item("grape", quantity=2)
    assert c.items() == {}

# remove_item: not in cart raises

def test_remove_nonexistent_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent")

# subtotal calculation with bulk discounts

def test_subtotal_with_bulk_discount():
    c = cart.Cart()
    # 12 apples -> 5% discount, price 1 each
    c.add_item("apple", unit_price=1.0, quantity=12)
    # 55 bananas -> 10% discount, price 2 each
    c.add_item("banana", unit_price=2.0, quantity=55)
    subtotal = (1.0 * 12) * (1 - cart.bulk_discount_percent(12)/100)
    subtotal += (2.0 * 55) * (1 - cart.bulk_discount_percent(55)/100)
    assert c.subtotal() == round_half_up(subtotal)

# total with coupon and shipping

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("item", unit_price=200.0, quantity=1)  # subtotal 200
    # Apply SAVE10 coupon => 180
    total_no_shipping = round_half_up(180)
    # shipping fee: 60 (not member)
    expected_total = round_half_up(total_no_shipping + cart.shipping_fee(total_no_shipping))
    assert c.total(coupon="SAVE10") == expected_total

# total for empty cart returns zero and no shipping

def test_total_empty_cart_no_shipping():
    c = cart.Cart()
    assert c.total() == 0.0

# total with member discount (shipping half)

def test_total_member_shipping_half_fee():
    c = cart.Cart()
    c.add_item("item", unit_price=1000, quantity=1)  # subtotal 1000 -> free shipping
    assert c.total(member=True) == 1000.0
    c2 = cart.Cart()
    c2.add_item("item", unit_price=800, quantity=1)
    # subtotal 800 => shipping 60 (half for member -> 30)
    expected = round_half_up(800 + 30)
    assert c2.total(member=True) == expected

# coupon parsing error propagates to total

def test_total_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item("item", unit_price=50, quantity=1)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
