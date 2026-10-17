import pytest
import cart

# ---------- apply_discount ---------------------------------------------------
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),  # example from spec
        (100, 0, 100.0),   # no discount
        (50, 100, 0.0),    # full discount
        (123.45, 7.89, round(123.45 * (1 - 7.89/100), 2)),
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# boundary and error cases for apply_discount
@pytest.mark.parametrize(
    "price",
    [-1, -0.01],
)
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize(
    "percent",
    [-1, -0.5, 100.1, 200],
)
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent -------------------------------------------
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (1, 0),
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
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -5, 3.14],
)
def test_bulk_discount_invalid_quantity_raises(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon -----------------------------------------------------
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        ("  SaVe30  ", 30),
        ("SaVe1", 1),
        ("SaVe50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# invalid codes
@pytest.mark.parametrize(
    "code",
    [
        "SAVE0",          # below 1
        "SAVE51",         # above 50
        "DISCOUNT10",     # wrong prefix
        "save",           # missing number
        "100",            # no SAVE
        "SAVEXX",         # non-digit
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee -----------------------------------------------------
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, 60),
        (999.99, True, 30),
        (1000, False, 0),
        (1200, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-1, -10],
)
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal, False)

# ---------- Cart class -------------------------------------------------------
@pytest.fixture
def empty_cart():
    return cart.Cart()

# add_item basic and bulk discount integration via total
def test_add_item_basic(empty_cart):
    c = empty_cart
    c.add_item("apple", 2.5, 3)
    assert c.items() == {"apple": 3}
    assert c.subtotal() == 7.5

# adding existing item with same price increases quantity
def test_add_existing_same_price(empty_cart):
    c = empty_cart
    c.add_item("banana", 1.0, 2)
    c.add_item("banana", 1.0, 3)
    assert c.items() == {"banana": 5}
    assert c.subtotal() == 5.0

# adding existing item with different price raises ValueError
def test_add_existing_different_price_raises(empty_cart):
    c = empty_cart
    c.add_item("orange", 1.2)
    with pytest.raises(ValueError):
        c.add_item("orange", 1.3)

# remove_item reduces quantity and removes when zero
def test_remove_item_behavior(empty_cart):
    c = empty_cart
    c.add_item("milk", 3.0, 4)
    c.remove_item("milk", 2)
    assert c.items() == {"milk": 2}
    c.remove_item("milk", 2)  # should remove completely
    assert c.items() == {}

# removing non-existent item raises KeyError
def test_remove_nonexistent_raises(empty_cart):
    with pytest.raises(KeyError):
        empty_cart.remove_item("nonexist")

# subtotal calculation from multiple items
def test_subtotal_multiple_items(empty_cart):
    c = empty_cart
    c.add_item("item1", 10, 2)  # 20
    c.add_item("item2", 5.5, 4)  # 22
    assert c.subtotal() == 42

# total calculation with member, coupon and bulk discounts
def test_total_with_all_discounts_and_shipping(empty_cart):
    c = empty_cart
    # item that qualifies for bulk discount
    c.add_item("widget", 10.0, 150)  # subtotal 1500 -> bulk discount 15%
    # another item without bulk discount
    c.add_item("gadget", 20.0, 1)
    # total before shipping: (1500*0.85)+(20)=1275+20=1295
    expected_subtotal = 1500 + 20
    expected_bulk_discounted = 1500 * 0.85 + 20
    assert c.subtotal() == expected_subtotal
    # apply coupon SAVE10 -> 10%
    total_after_coupon = round(expected_bulk_discounted * (1 - 10/100), 2)
    # member pays half shipping: subtotal >=1000 so free shipping
    final_expected = total_after_coupon + cart.shipping_fee(c.subtotal(), member=True)
    assert c.total(member=True, coupon="SAVE10") == final_expected

# total with no member and free shipping threshold not met
def test_total_no_member_shipping_charge(empty_cart):
    c = empty_cart
    c.add_item("paper", 5.0, 50)  # subtotal 250 -> bulk discount 10% => 225
    # coupon SAVE20 => 20%
    expected_after_bulk = 250 * 0.90
    total_after_coupon = round(expected_after_bulk * (1 - 20/100), 2)
    shipping = cart.shipping_fee(c.subtotal(), member=False)  # subtotal 250 < 1000 -> 60
    final_expected = total_after_coupon + shipping
    assert c.total(member=False, coupon="SAVE20") == final_expected

# total when no items: subtotal 0 and shipping free
def test_total_empty_cart(empty_cart):
    assert empty_cart.subtotal() == 0
    assert empty_cart.total() == 0
