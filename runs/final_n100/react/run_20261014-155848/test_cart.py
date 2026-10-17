import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# ---- apply_discount ----

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

def test_apply_discount_zero_percent():
    assert apply_discount(100, 0) == 100.0

def test_apply_discount_max_percent():
    assert apply_discount(50, 100) == 0.0

def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        apply_discount(-5, 10)

def test_apply_discount_invalid_percent():
    for p in (-1, 101):
        with pytest.raises(ValueError):
            apply_discount(100, p)

# ---- bulk_discount_percent ----

def test_bulk_discount_percent_none():
    assert bulk_discount_percent(5) == 0

def test_bulk_discount_percent_small():
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5

def test_bulk_discount_percent_medium():
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10

def test_bulk_discount_percent_large():
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(200) == 15

def test_bulk_discount_percent_invalid():
    with pytest.raises(ValueError):
        bulk_discount_percent(0)
    with pytest.raises(ValueError):
        bulk_discount_percent(-3)

# ---- parse_coupon ----

def test_parse_coupon_valid_simple():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20") == 20
    assert parse_coupon(" SAVE30 ") == 30

def test_parse_coupon_invalid_format():
    with pytest.raises(ValueError):
        parse_coupon("SAVEXY")
    with pytest.raises(ValueError):
        parse_coupon("DISCOUNT10")

# ---- shipping_fee ----

def test_shipping_free_for_large_subtotal():
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500) == 0

def test_shipping_non_member():
    assert shipping_fee(200) == 60
    assert shipping_fee(999.99) == 60

def test_shipping_member_half_fee():
    assert shipping_fee(200, member=True) == 30
    assert shipping_fee(0, member=True) == 30

def test_shipping_invalid_subtotal():
    with pytest.raises(ValueError):
        shipping_fee(-1)

# ---- Cart class ----

def test_cart_initial_empty():
    c = Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 60  # non-member, subtotal 0 => fee 60

def test_cart_add_and_remove_items():
    c = Cart()
    c.add_item("apple", 1.00)
    assert c.items()["apple"] == (1.00, 1)
    c.add_item("banana", 2.50, quantity=3)
    assert c.items()["banana"] == (2.50, 3)
    # subtotal
    assert c.subtotal() == 1*1.00 + 3*2.50
    # remove one banana
    c.remove_item("banana", quantity=1)
    assert c.items()["banana"] == (2.50, 2)
    # removing more than existing should raise error
    with pytest.raises(KeyError):
        c.remove_item("apple", quantity=5)

# total with coupon and member discounts

def test_cart_total_with_member_and_coupon():
    c = Cart()
    c.add_item("widget", 100, quantity=10)  # triggers 5% bulk discount on widget price
    subtotal_before_discounts = 100*10
    # Bulk discount percent: 5 -> 95.0 each after discount
    assert cart.bulk_discount_percent(10) == 5
    expected_item_total = round(100 * (1-0.05) * 10, 2)
    # apply coupon SAVE10 gives 10% off on subtotal
    final_after_coupon = round(expected_item_total * (1-0.10), 2)
    # member pays half shipping fee (30) because subtotal before shipping is <1000
    expected_total = round(final_after_coupon + 30, 2)
    assert c.total(member=True, coupon="SAVE10") == expected_total

# total without any discounts

def test_cart_total_without_discounts():
    c = Cart()
    c.add_item("item", 5, quantity=4)  # subtotal 20
    assert c.total() == 80.0  # 60 shipping fee + 20 items
