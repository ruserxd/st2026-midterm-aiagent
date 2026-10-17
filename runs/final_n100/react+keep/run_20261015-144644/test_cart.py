import pytest
import cart

# Helper for creating a cart with a single item

def make_cart(name="item", unit_price=10, quantity=1):
    c = cart.Cart()
    c.add_item(name, unit_price, quantity)
    return c

# ----------------- Tests for apply_discount -----------------

test_cases_apply_discount = [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
]

@pytest.mark.parametrize("price,percent,expected", test_cases_apply_discount)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# Negative price
with pytest.raises(ValueError):
    cart.apply_discount(-1, 10)
# Percent out of range
for bad_percent in (-5, 101):
    with pytest.raises(ValueError):
        cart.apply_discount(100, bad_percent)

# ----------------- Tests for bulk_discount_percent -----------------

test_cases_bulk = [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
]

@pytest.mark.parametrize("qty,expected", test_cases_bulk)
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

with pytest.raises(ValueError):
    cart.bulk_discount_percent(0)
with pytest.raises(ValueError):
    cart.bulk_discount_percent(-3)

# ----------------- Tests for parse_coupon -----------------

test_coupons = [("SAVE10", 10), ("save20 ", 20), ("  SaVe50  ", 50)]

@pytest.mark.parametrize("code,expected", test_coupons)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

invalid_codes = ["SAVE0", "SAVEX10", "NOTACODE", "", "SA VE10"]
for ic in invalid_codes:
    with pytest.raises(ValueError):
        cart.parse_coupon(ic)

# ----------------- Tests for shipping_fee -----------------

def test_shipping_fee_free():
    assert cart.shipping_fee(1000) == 0.0
    assert cart.shipping_fee(2000) == 0.0

def test_shipping_fee_regular_and_member():
    assert cart.shipping_fee(500, member=False) == 60.0
    assert cart.shipping_fee(500, member=True) == 30.0

with pytest.raises(ValueError):
    cart.shipping_fee(-10)

# ----------------- Tests for Cart class methods -----------------

def test_cart_initial_state():
    c = cart.Cart()
    assert list(c.items().keys()) == []
    assert c.subtotal() == 0.0
    assert c.total() == 0.0

def test_add_and_subtotal_without_bulk_discount():
    c = make_cart("apple", unit_price=2, quantity=3)
    assert c.items() == {"apple": 3}
    # no bulk discount applied
    assert c.subtotal() == 6.0

def test_add_multiple_same_item_and_discounts():
    c = cart.Cart()
    c.add_item("widget", 10, quantity=5)
    c.add_item("widget", 10, quantity=3)  # total 8 - bulk discount 5%
    assert c.items() == {"widget": 8}
    expected_before_discount = 10 * 8
    discount_percent = cart.bulk_discount_percent(8)
    after_bulk = expected_before_discount * (1 - discount_percent/100.0)
    assert pytest.approx(c.subtotal(), 2) == round(after_bulk, 2)

def test_remove_item_and_removal_when_zero():
    c = make_cart("gadget", 15, quantity=4)
    c.remove_item("gadget", quantity=2)
    assert c.items() == {"gadget": 2}
    # removing more than exists should reduce to zero but not raise error
    c.remove_item("gadget", quantity=5)
    assert "gadget" not in c.items()

# Test adding item with different price raises error
with pytest.raises(ValueError):
    c = cart.Cart()
    c.add_item("item1", 5, 2)
    # attempt to add same name but different price
    c.add_item("item1", 6, 1)

# Test total with coupon and shipping
c = make_cart("book", unit_price=30, quantity=3)  # subtotal 90 no bulk discount
assert cart.parse_coupon("SAVE10") == 10
expected_total = round(90 * 0.9 + 60, 2)
assert c.total(coupon="SAVE10") == expected_total  # shipping applied after discount
# member should get half shipping after coupon
c_member = make_cart("pen", unit_price=5, quantity=2)
subtotal = 10.0
expected_member_total = round(subtotal * 0.95 + 30, 2)
assert c_member.total(coupon="SAVE5", member=True) == expected_member_total
