import pytest
import cart

# ----- helper fixtures and helpers -------------------------------------------------

def round_two(x):
    return round(float(x), 2)

# ----- tests for helper functions -----------------------------------------------

@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200.0, 15, 170.0),   # example from spec
        (100.0, 0, 100.0),    # no discount
        (150.5, 33.3, round_two(150.5 * (1 - 33.3/100))),
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "quantity,expected",
    [
        (9, 0),   # less than 10
        (10, 5),  # threshold
        (49, 5),  # just below next tier
        (50, 10), # new tier
        (99, 10),
        (100, 15),# top tier
        (250, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        ("  SaVe5  ", 5),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "SAVEx",          # non numeric
        "SAVEBLAH",       # no number
        "10SAVE",         # wrong order
        "SA 5",           # space inside prefix
        "",               # empty string
        "save0",          # out of range <1
        "save51",         # >50
        "save-5",         # negative
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),   # below free threshold
        (500, True, 30),  # member half
        (1000, False, 0), # free shipping
        (1500, True, 0),  # still free
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# ----- Cart class tests ----------------------------------------------------------

@pytest.fixture
def empty_cart():
    return cart.Cart()

@pytest.fixture
def populated_cart(empty_cart):
    # add 3 items of varying quantities to trigger bulk discounts
    empty_cart.add_item("widget", unit_price=10.0, quantity=5)   # no bulk
    empty_cart.add_item("gadget", unit_price=20.0, quantity=12)  # 5% bulk on this item
    empty_cart.add_item("thingamajig", unit_price=30.0, quantity=55)  # 10% bulk
    return empty_cart

# Test that items() returns the expected structure and discounts applied to each line

def test_items_return_structure(populated_cart):
    items = populated_cart.items()
    assert isinstance(items, list)
    # We expect three entries in the same order added
    names = [i["name"] for i in items]
    assert names == ["widget", "gadget", "thingamajig"]
    # Check individual line totals after bulk discount
    # widget: 5 * 10 = 50, no bulk => 50.0
    # gadget: 12 * 20 = 240, bulk 5% -> 228.0
    # thingamajig: 55 * 30 = 1650, bulk 10% -> 1485.0
    expected_totals = [50.0, 228.0, 1485.0]
    for i, exp in zip(items, expected_totals):
        assert round_two(i["total_price_after_discount"]) == exp

# subtotal() should be the sum of line totals before shipping and coupons

def test_subtotal(populated_cart):
    assert populated_cart.subtotal() == 50.0 + 228.0 + 1485.0

# total without coupon or member, expect shipping applied to subtotal

def test_total_basic(populated_cart):
    # subtotal is >1000 so shipping free
    assert populated_cart.total(member=False, coupon=None) == round_two(50+228+1485)

# total with a valid coupon applied after subtotal (before shipping)

def test_total_with_coupon(populated_cart):
    # use a 10% coupon: subtract 10% of subtotal
    expected_after_coupon = round_two((50+228+1485) * 0.9)
    assert populated_cart.total(member=False, coupon="SAVE10") == expected_after_coupon

# total for member should apply half shipping fee if applicable

def test_total_member_shipment(populated_cart):
    # subtotal >1000 so no shipping even for member; ensure same as non-member
    assert populated_cart.total(member=True, coupon=None) == round_two(50+228+1485)

# total on empty cart should be zero

def test_total_empty_cart(empty_cart):
    assert empty_cart.total() == 0.0

# removing items reduces subtotal accordingly

def test_remove_item(populated_cart):
    # remove two gadgets, quantity goes from 12 to 10 -> still bulk discount applies
    populated_cart.remove_item("gadget", quantity=2)
    new_subtotal = 50.0 + (10 * 20) * 0.95 + 1485.0
    assert round_two(populated_cart.subtotal()) == round_two(new_subtotal)
