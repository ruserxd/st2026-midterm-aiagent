import pytest
import cart

# --- bulk discount percent tests ---
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (99, 10),
        (100, 15),
        (49, 5),
        (50, 10),
        (9, 0),
        (10, 5),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# --- apply_discount tests ---
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),
        (0, 0, 0.0),
        (100, 0, 100.0),
        (100, 100, 0.0),
        (123.45, 20, round(123.45 * 0.8, 2)),
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price,percent",
    [(-1, 10), (0, -5), (0, 101)],
)
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --- parse_coupon tests ---
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save5", 5),
        (" SAVE20 ", 20),
        ("SaVe50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    ["SAV10", "SAVE0", "SAVE51", "ABC10", "SAVE-5", "SAVE50x"],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee tests ---
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (1000, False, 0),
        (999.99, False, 60),
        (500, True, 30),
        (1200, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-10, -1],
)
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --- Cart class tests ---

def test_add_item_and_items():
    c = cart.Cart()
    c.add_item("apple", 1.0, 2)
    assert c.items() == {"apple": 2}
    # add same item increases quantity
    c.add_item("apple", 1.0, 3)
    assert c.items() == {"apple": 5}
    # adding different unit price should raise ValueError
    with pytest.raises(ValueError):
        c.add_item("apple", 2.0, 1)


def test_add_invalid_parameters():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("banana", -1, 1)
    with pytest.raises(ValueError):
        c.add_item("banana", 1, 0)
    with pytest.raises(ValueError):
        c.add_item("banana", 1, "2")


def test_remove_item_logic():
    c = cart.Cart()
    c.add_item("orange", 1.5, 3)
    c.remove_item("orange", 2)
    assert c.items() == {"orange": 1}
    # removing remaining quantity should delete the item
    c.remove_item("orange", 1)
    with pytest.raises(KeyError):
        _ = c.items()["orange"]
    # Removing non-existent item raises KeyError
    with pytest.raises(KeyError):
        c.remove_item("banana")


def test_subtotal_calculation():
    c = cart.Cart()
    c.add_item("widget", 10.0, 5)   # bulk discount 5%
    expected_line = 10.0 * 5 * (1 - 0.05)
    c.add_item("gadget", 20.0, 12)  # bulk discount 5% for 12
    expected_gadget = 20.0 * 12 * (1 - 0.05)
    assert c.subtotal() == round(expected_line + expected_gadget, 2)
    # empty cart subtotal
    c_empty = cart.Cart()
    assert c_empty.subtotal() == 0


def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("item", 200.0, 1)  # subtotal 200
    # No coupon, non-member: shipping fee 60 => total 260
    assert c.total(member=False) == round(200 + 60, 2)
    # Member gets half shipping
    assert c.total(member=True) == round(200 + 30, 2)
    # With a coupon SAVE10 (10% off), amount after discount = 180; still needs shipping fee 60 => total 240
    assert c.total(coupon="SAVE10") == round(180 + 60, 2)
    # Coupon that reduces subtotal below 1000 but not free: e.g., subtotal 1500 with SAVE50 gives 750 -> shipping fee 60
    c2 = cart.Cart()
    c2.add_item("mega", 500.0, 3)  # 1500
    assert c2.total(coupon="SAVE50") == round(750 + 60, 2)
