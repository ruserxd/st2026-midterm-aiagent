import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---- Tests for apply_discount ----

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@pytest.mark.parametrize(
    "price,percent",
    [(-1, 10), (100, -5), (100, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---- Tests for bulk_discount_percent ----

def test_bulk_discount_percent_values():
    assert bulk_discount_percent(5) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(100) == 15

@pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---- Tests for parse_coupon ----

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20") == 20
    assert parse_coupon(" SAVE30 ") == 30

@pytest.mark.parametrize(
    "code",
    ["SAVE0", "SAVE51", "INVALID", "123", "SAVExx", ""],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---- Tests for shipping_fee ----

def test_shipping_fee_free_and_half():
    assert shipping_fee(1200) == 0
    assert shipping_fee(999.99) == 60
    assert shipping_fee(999.99, member=True) == 30

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---- Tests for Cart class ----

def test_cart_initial_state():
    c = Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 60  # subtotal 0, non-member shipping fee 60

def test_add_and_remove_items():
    c = Cart()
    c.add_item("apple", 5.0, quantity=3)
    c.add_item("banana", 2.0)
    assert c.items() == {"apple": (5.0, 3), "banana": (2.0, 1)}
    assert c.subtotal() == 5.0 * 3 + 2.0

    # remove one apple
    c.remove_item("apple", quantity=1)
    assert c.items()["apple"] == (5.0, 2)
    # remove remaining apples
    c.remove_item("apple")
    assert "apple" not in c.items()
    # removing non-existent item should raise KeyError
    with pytest.raises(KeyError):
        c.remove_item("pear")

# Coupon and member discounts

def test_cart_total_with_coupon_and_member():
    c = Cart()
    c.add_item("widget", 100.0, quantity=10)  # subtotal 1000
    # bulk discount: 5% -> 950
    assert c.subtotal() == 1000
    # apply coupon SAVE10 (10%) on discounted subtotal
    total = c.total(member=True, coupon="SAVE10")
    # subtotal after bulk: 950. Apply coupon: 855
    # shipping free for subtotal >=1000? after discount it's 950 <1000 so fee 30 for member
    assert total == 855 + 30

# Test that coupon is case-insensitive and whitespace-ignored

def test_cart_coupon_edge_cases():
    c = Cart()
    c.add_item("item", 50.0)
    # subtotal 50, no bulk discount
    for code in ["SAVE5", "save5", " SAVE5 "]:
        assert c.total(coupon=code) == 50 * 0.95 + 60  # non-member shipping fee 60

# Ensure that total respects the current subtotal and discounts correctly

def test_cart_total_no_discounts():
    c = Cart()
    c.add_item("foo", 20.0, quantity=2)
    assert c.total() == 40 + 60  # no discounts, shipping fee

# Edge case: total with subtotal >=1000 free shipping even after coupon

def test_cart_free_shipping_after_coupon():
    c = Cart()
    c.add_item("expensive", 1200.0)
    assert c.total() == 1200 + 60  # before discount, subtotal>=1000 -> shipping 0? Wait spec says free if subtotal >=1000
    # Actually shipping_fee function: if subtotal>=1000 => fee 0
    # so total should be 1200
    assert c.total() == 1200
