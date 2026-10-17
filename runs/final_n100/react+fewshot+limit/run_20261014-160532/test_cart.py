import pytest
import cart

# Helper to format rounded values

def round2(x):
    return round(float(x), 2)

# ---------- apply_discount ----------

test_cases_apply = [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
]

@pytest.mark.parametrize("price,percent,expected", test_cases_apply)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# boundary and error cases

def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        cart.apply_discount(-1, 10)


def test_apply_discount_invalid_percent_low():
    with pytest.raises(ValueError):
        cart.apply_discount(100, -5)


def test_apply_discount_invalid_percent_high():
    with pytest.raises(ValueError):
        cart.apply_discount(100, 105)

# ---------- bulk_discount_percent ----------

cases_bulk = [
    (1, 0),
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
]

@pytest.mark.parametrize("qty,expected", cases_bulk)
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

# error for non-positive quantity

def test_bulk_discount_invalid_qty():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)

# ---------- parse_coupon ----------

coupon_cases = [
    ("SAVE10", 10),
    ("save5", 5),
    (" SAVE25 ", 25),
]

@pytest.mark.parametrize("code,expected", coupon_cases)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# invalid codes

def test_parse_coupon_invalid_non_numerical():
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVEx")

def test_parse_coupon_invalid_prefix():
    with pytest.raises(ValueError):
        cart.parse_coupon("DIS10")

def test_parse_coupon_invalid_whitespace_only():
    with pytest.raises(ValueError):
        cart.parse_coupon("   ")

# out of range percent

def test_parse_coupon_out_of_range_low():
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE0")

def test_parse_coupon_out_of_range_high():
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE51")

# ---------- shipping_fee ----------

shipping_cases = [
    (500, 60),      # non-member
    (1000, 0),     # free at threshold
    (2000, 0),
]

@pytest.mark.parametrize("subtotal,expected", shipping_cases)
def test_shipping_fee(subtotal, expected):
    assert cart.shipping_fee(subtotal) == expected

# member half

def test_shipping_member_half():
    assert cart.shipping_fee(500, member=True) == 30.0

# invalid subtotal negative

def test_shipping_invalid_subtotal():
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

# ---------- Cart class behaviours ----------

def test_cart_initial_state_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 0.0


def test_add_and_remove_items():
    c = cart.Cart()
    c.add_item("apple", 1.5, 3)
    assert c.items() == {"apple": 3}
    # adding same item increases quantity
    c.add_item("apple", 1.5, 2)
    assert c.items() == {"apple": 5}
    # add another item
    c.add_item("banana", 0.8, 4)
    assert c.items() == {"apple": 5, "banana": 4}
    # remove part of quantity
    c.remove_item("apple", 2)
    assert c.items() == {"apple": 3, "banana": 4}
    # removing more than existing removes the item entirely
    c.remove_item("banana", 5)
    assert c.items() == {"apple": 3}
    # remove remaining quantity to delete
    c.remove_item("apple", 3)
    assert c.items() == {}


def test_add_same_name_different_price_raises():
    c = cart.Cart()
    c.add_item("widget", 10.0, 1)
    with pytest.raises(ValueError):
        c.add_item("widget", 12.0, 2)


def test_invalid_unit_price_and_quantity_on_add():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("gadget", -5, 1)
    with pytest.raises(ValueError):
        c.add_item("gadget", 5, 0)


def test_remove_nonexistent_item_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexist", 1)

# subtotal calculation with bulk discounts

def test_subtotal_with_bulk_discount():
    c = cart.Cart()
    # 12 units, should get 5% discount on that item
    c.add_item("tshirt", 20.0, 12)
    expected_before = 20.0 * 12 * (1 - 0.05)  # 240 * 0.95 = 228.0
    assert round2(c.subtotal()) == round2(expected_before)


def test_subtotal_empty_cart():
    c = cart.Cart()
    assert c.subtotal() == 0.0

# total calculation with coupon and shipping

def test_total_no_coupon_member_false():
    c = cart.Cart()
    c.add_item("item", 100.0, 1)
    # subtotal 100, no discount
    # shipping 60 because subtotal < 1000 and member=False
    expected = round2(100 + 60)
    assert c.total() == expected


def test_total_with_coupon_and_member():
    c = cart.Cart()
    c.add_item("item", 200.0, 1)
    # subtotal 200, coupon SAVE10 -> 180
    # shipping 60 (member=False) applied to 180 -> 240 total
    assert c.total(coupon="SAVE10") == round2(180 + 60)


def test_total_shipping_free_on_high_subtotal():
    c = cart.Cart()
    c.add_item("expensive", 1000.0, 1)
    # subtotal 1000 => free shipping, total 1000
    assert c.total() == round2(1000.0 + 0)

# ensure coupon invalid raises

def test_total_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item("item", 50.0, 1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# ensure empty cart no shipping

def test_empty_cart_no_shipping_fee():
    c = cart.Cart()
    assert c.total() == 0.0
