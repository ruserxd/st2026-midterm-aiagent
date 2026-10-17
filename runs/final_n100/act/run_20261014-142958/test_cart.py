import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount ----------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0
    # No rounding needed for whole numbers
    assert apply_discount(100, 10) == 90.0


def test_apply_discount_rounding():
    # Should round to two decimals
    assert apply_discount(99.999, 50) == pytest.approx(49.9995)
    assert apply_discount(123.4567, 25) == pytest.approx(92.5929)


def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        apply_discount(-1, 10)


def test_apply_discount_invalid_percent():
    for bad in [-5, 101]:
        with pytest.raises(ValueError):
            apply_discount(100, bad)

# ---------- bulk_discount_percent ----------

def test_bulk_discount_percent_limits():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15


def test_bulk_discount_percent_invalid():
    for bad in [0, -1, 2.5]:
        with pytest.raises(ValueError):
            bulk_discount_percent(bad)

# ---------- parse_coupon ----------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save50") == 50
    assert parse_coupon("   SaVe25  ") == 25


def test_parse_coupon_invalid_format():
    for bad in ["SAVEX", "DISCOUNT20", "save0", "SAVE51", "", "123"]:
        with pytest.raises(ValueError):
            parse_coupon(bad)

# ---------- shipping_fee ----------

def test_shipping_fee_free_and_paid():
    assert shipping_fee(1000) == 0
    assert shipping_fee(999.99) == 60
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(1500, member=False) == 0


def test_shipping_fee_invalid_subtotal():
    with pytest.raises(ValueError):
        shipping_fee(-10)

# ---------- Cart class ----------

def test_cart_initially_empty():
    c = Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0


def test_add_and_remove_items():
    c = Cart()
    c.add_item("apple", 5, quantity=3)
    assert c.items()["apple"] == {"unit_price": 5, "quantity": 3}
    assert c.subtotal() == 15

    # Add more of same item
    c.add_item("apple", 5, quantity=2)
    assert c.items()["apple"]["quantity"] == 5
    assert c.subtotal() == 25

    # Remove some quantity
    c.remove_item("apple", quantity=4)
    assert c.items()["apple"]["quantity"] == 1
    assert c.subtotal() == 5

    # Removing more than present should raise ValueError
    with pytest.raises(ValueError):
        c.remove_item("apple", quantity=2)

    # Remove remaining item
    c.remove_item("apple")
    assert "apple" not in c.items()


def test_cart_total_with_discounts_and_shipping():
    c = Cart()
    c.add_item("itemA", 200, quantity=10)   # triggers bulk discount of 5%
    # subtotal before discounts: 2000
    expected_subtotal = 2000
    assert c.subtotal() == expected_subtotal

    # total without member or coupon
    # Apply bulk discount percent to each item? Implementation likely applies per-item.
    # We'll compute expected manually: unit price after 5% => 190, *10 = 1900
    expected_total_no_member = apply_discount(expected_subtotal, bulk_discount_percent(10))
    # Add shipping fee (30 because member False and subtotal >1000? actually subtotal 2000 >=1000 free)
    assert c.total() == pytest.approx(expected_total_no_member)  # shipping should be zero

    # Now with coupon SAVE20 on total
    coupon_discount = parse_coupon("SAVE20")
    after_coupon = apply_discount(expected_subtotal, bulk_discount_percent(10))
    after_coupon = apply_discount(after_coupon, coupon_discount)
    assert c.total(coupon="SAVE20") == pytest.approx(after_coupon)

    # Member discount (members get half shipping but no free shipping here)
    # Let's create a cart below 1000 to trigger shipping
    d = Cart()
    d.add_item("itemB", 300, quantity=2)   # subtotal 600, bulk discount none
    assert d.total(member=True) == pytest.approx(
        apply_discount(600, 0) + shipping_fee(600, member=True)
    )

# End of tests
