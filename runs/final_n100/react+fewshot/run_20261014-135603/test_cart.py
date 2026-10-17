import pytest
import cart

# Helper for roundings

def almost_eq(a, b):
    return abs(a - b) < 1e-9

# --- apply_discount -----------------------------------------------------
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200.0, 15, 170.0),            # example from spec
        (100.0, 0, 100.0),             # no discount
        (50.0, 100, 0.0),              # full discount
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# error cases for apply_discount
@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", ["a", -5, 150])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100.0, percent)

# --- bulk_discount_percent ----------------------------------------------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (9, 0),      # below 10
        (10, 5),     # boundary 10
        (49, 5),     # just before 50
        (50, 10),    # boundary 50
        (99, 10),    # just before 100
        (100, 15),   # boundary 100
        (150, 15),   # above 100
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 2.5])
def test_bulk_discount_percent_invalid_raises(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --- parse_coupon -------------------------------------------------------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save25", 25),          # case-insensitive
        (" SAVE5 ", 5),           # surrounding whitespace
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# boundary N values
@pytest.mark.parametrize("code", ["SAVE1", "SAVE50"])
def test_parse_coupon_boundary_values(code):
    # should not raise
    cart.parse_coupon(code)

# invalid codes: wrong prefix, out of range, non-integer suffix
@pytest.mark.parametrize(
    "code",
    [
        "save0",     # N < 1
        "SAVE51",    # N > 50
        "SAVExx",    # non-digit suffix
        "DISCOUNT10",  # wrong prefix
        "" ,         # empty
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee -------------------------------------------------------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),          # below threshold
        (999.99, True, 30),      # member gets half
        (1000, False, 0),        # free shipping threshold
        (1500, True, 0),         # still free for members
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --- Cart class ----------------------------------------------------------
def test_cart_initially_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 0.0

def test_add_item_and_items_dict():
    c = cart.Cart()
    c.add_item("apple", 2.5)
    c.add_item("banana", 1.2, quantity=3)
    assert c.items() == {"apple": 1, "banana": 3}

# adding same item increases quantity, unit_price must match

def test_add_same_item_increases_quantity():
    c = cart.Cart()
    c.add_item("pear", 0.99)
    c.add_item("pear", 0.99, quantity=4)
    assert c.items() == {"pear": 5}

# mismatched unit price raises ValueError

def test_add_same_item_mismatched_price_raises():
    c = cart.Cart()
    c.add_item("orange", 1.0)
    with pytest.raises(ValueError):
        c.add_item("orange", 1.2)

# invalid unit price or quantity raises ValueError
@pytest.mark.parametrize(
    "unit_price,quantity",
    [(-1, 1), (1.0, 0), (1.5, -3), ("a", 2)],
)
def test_add_item_invalid_inputs(unit_price, quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("test", unit_price, quantity=quantity)

# remove_item decreases quantity and removes when zero or less

def test_remove_item_decrease_and_remove():
    c = cart.Cart()
    c.add_item("mango", 3.0, quantity=5)
    c.remove_item("mango", quantity=2)
    assert c.items() == {"mango": 3}
    # remove remaining 3 (or more) removes the item completely
    c.remove_item("mango", quantity=4)
    assert "mango" not in c.items()

# removing non-existent key raises KeyError

def test_remove_nonexistent_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("ghost")

# subtotal calculation with bulk discounts

def test_subtotal_with_bulk_discount():
    c = cart.Cart()
    # 10 units, should get 5% discount on each item
    c.add_item("widget", 100.0, quantity=10)
    expected = 100.0 * 10 * (1 - 0.05)   # 950.0
    assert almost_eq(c.subtotal(), round(expected, 2))

# subtotal rounding to two decimals

def test_subtotal_rounding():
    c = cart.Cart()
    c.add_item("toy", 19.99, quantity=3)
    # no bulk discount (quantity <10)
    expected = 19.99 * 3
    assert almost_eq(c.subtotal(), round(expected, 2))

# total calculation with coupon and shipping fee

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("item", 500.0)
    # subtotal 500
    # apply coupon SAVE10 -> 10% off => 450
    # shipping fee for 450 (member=False) => 60
    # total = 510.00
    assert almost_eq(c.total(member=False, coupon="SAVE10"), 510.0)

# total with member shipping discount and no coupon

def test_total_member_free_shipping():
    c = cart.Cart()
    c.add_item("expensive", 1200.0)
    # subtotal >1000 => free shipping, even for non-member
    assert almost_eq(c.total(member=False), 1200.0)

# total with empty cart should be zero and no shipping

def test_total_empty_cart_zero_shipping():
    c = cart.Cart()
    assert almost_eq(c.total(), 0.0)

# coupon parsing error propagates in total

def test_total_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item("item", 100.0)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
