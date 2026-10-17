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

@pytest.mark.parametrize("price,percent,result", [
    (100, 0, 100.0),
    (100, 100, 0.0),
])
def test_apply_discount_edge_cases(price, percent, result):
    assert apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [
    (-1, 10),
    (100, -5),
    (100, 105),
])
def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent tests ----------

def test_bulk_discount_percent_branches():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon tests ----------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save50") == 50
    assert parse_coupon(" SAVE20 ") == 20
    # boundary values
    assert parse_coupon("SAVE1") == 1
    assert parse_coupon("SAVE50") == 50

@pytest.mark.parametrize("code", [
    "",
    "SAV10",
    "SAVE0",
    "SAVE51",
    "SAVE-5",
    "abc123",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee tests ----------

def test_shipping_fee_basic():
    assert shipping_fee(1200) == 0
    assert shipping_fee(999.99) == 60
    assert shipping_fee(0) == 60

# member discount
for subtotal in [500, 1000, 0]:
    expected = 0 if subtotal >= 1000 else 30
    assert shipping_fee(subtotal, member=True) == expected

@pytest.mark.parametrize("subtotal", [-1, -50])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class tests ----------

def test_cart_initial_state():
    c = Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 60.0  # shipping fee with empty cart


def test_add_and_remove_items():
    c = Cart()
    c.add_item("apple", 1.5, quantity=4)
    c.add_item("banana", 2.0)
    assert c.items()["apple"] == (1.5, 4)
    assert c.items()["banana"] == (2.0, 1)

    # subtotal calculation
    expected_subtotal = 1.5*4 + 2.0
    assert c.subtotal() == pytest.approx(expected_subtotal)

    # remove items partially
    c.remove_item("apple", quantity=2)
    assert c.items()["apple"] == (1.5, 2)

    # removing more than present should raise ValueError
    with pytest.raises(ValueError):
        c.remove_item("apple", quantity=5)

    # remove last unit
    c.remove_item("banana")
    assert "banana" not in c.items()


def test_cart_total_with_discounts_and_coupons():
    c = Cart()
    c.add_item("widget", 100, quantity=10)  # triggers bulk discount of 5%
    subtotal_before_discount = 100 * 10
    # bulk discount applies to the item before coupon
    expected_bulk_disc = apply_discount(subtotal_before_discount, bulk_discount_percent(10))
    assert c.subtotal() == pytest.approx(expected_bulk_disc)

    # total without coupon or member
    assert c.total() == pytest.approx(c.subtotal() + 60.0)

    # apply a valid coupon
    coupon_value = parse_coupon("SAVE10")
    discounted_subtotal = apply_discount(c.subtotal(), coupon_value)
    expected_total = discounted_subtotal + 60.0
    assert c.total(coupon="SAVE10") == pytest.approx(expected_total)

    # member discount halves shipping fee
    assert c.total(member=True) == pytest.approx(c.subtotal() + 30.0)

    # combined member and coupon
    expected = discounted_subtotal + 30.0
    assert c.total(member=True, coupon="SAVE10") == pytest.approx(expected)

# Edge case: total when subtotal >= 1000 (free shipping)

def test_cart_free_shipping():
    c = Cart()
    c.add_item("expensive", 200, quantity=6)  # 1200 subtotal before discount
    assert c.total() == pytest.approx(c.subtotal())  # shipping zero
    assert c.total(member=True) == pytest.approx(c.subtotal())
    # coupon still applies to subtotal
    discounted = apply_discount(c.subtotal(), parse_coupon("SAVE5"))
    assert c.total(coupon="SAVE5") == pytest.approx(discounted)
