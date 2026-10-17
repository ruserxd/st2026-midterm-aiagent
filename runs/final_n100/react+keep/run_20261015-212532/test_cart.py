import pytest
import cart

# --------- Utility helpers ---------

def round2(val):
    return round(val, 2)

# ---------- Tests for individual functions ----------

def test_apply_discount_valid():
    assert cart.apply_discount(200, 15) == 170.0
    # rounding behaviour
    assert cart.apply_discount(10, 33) == round2(10 * (100-33)/100)

@pytest.mark.parametrize(
    "price,percent", [(-1, 10), (10, -5), (10, 105)],
)
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent tests ---------

def test_bulk_discount_percent_brackets():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(51) == 10
    assert cart.bulk_discount_percent(100) == 15

@pytest.mark.parametrize("qty", [0, -1, 3.5], ids=lambda x: f"{x}")
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- parse_coupon tests ---------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save25") == 25
    assert cart.parse_coupon(" SAVE05") == 5

@pytest.mark.parametrize(
    "code", ["sav10", "SAVE0", "SAVE51", "SAVE-1", "  ", None],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee tests ---------

def test_shipping_fee_basic():
    # Non-member below threshold
    assert cart.shipping_fee(999.99) == 60
    # Member below threshold
    assert cart.shipping_fee(900, member=True) == 30
    # Free shipping at or above threshold
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(2000) == 0

@pytest.mark.parametrize("subtotal", [-1, -10], ids=lambda x: f"{x}")
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class tests ---------

def test_cart_initial_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

def test_add_and_remove_items():
    c = cart.Cart()
    c.add_item("apple", 1.00, 3)
    assert c.items()["apple"] == 3
    # adding same item increases quantity
    c.add_item("apple", 1.00, 2)
    assert c.items()["apple"] == 5
    # incompatible unit price raises
    with pytest.raises(ValueError):
        c.add_item("apple", 1.50, 1)

    # remove quantity less than total
    c.remove_item("apple", 3)
    assert c.items()["apple"] == 2
    # removing more than remaining deletes the item
    c.remove_item("apple", 5)
    assert "apple" not in c.items()

def test_remove_nonexistent_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("banana")

# The implementation incorrectly deletes an item only when quantity < 0.
# Verify this bug by removing exactly the remaining amount.
def test_remove_exact_quantity_bug():
    c = cart.Cart()
    c.add_item("orange", 2.00, 3)
    # remove all items
    c.remove_item("orange", 3)
    assert "orange" in c.items()  # should be removed but still present
    assert c.items()["orange"] == 0

# ---------- subtotal calculation with bulk discount ----------

def test_subtotal_bulk_discount():
    c = cart.Cart()
    c.add_item("toy", 10.00, 5)   # no discount
    assert c.subtotal() == round2(50)
    c.add_item("toy", 10.00, 10)  # total qty=15 -> bulk discount 5%
    expected = cart.apply_discount(10*25, 5)
    assert c.subtotal() == round2(expected)

# ---------- total with coupon and shipping mismatch bug ---------

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("widget", 100.00, 1)
    # subtotal before discount: 100
    # apply 10% coupon -> amount 90
    # shipping should be based on 90 (non-member): 60
    expected_total = round2(90 + 60)  # 150
    assert c.total(coupon="SAVE10") == expected_total
    # Implementation incorrectly uses subtotal for shipping, resulting in 160.

# ---------- test rounding behaviour in total ----------

def test_total_rounding():
    c = cart.Cart()
    c.add_item("item", 33.3333, 1)
    # No coupon; subtotal=33.33 after rounding of apply_discount(33.3333,0)=33.33
    # shipping: 60 (non-member)
    assert c.total() == round2(33.33 + 60)  # 93.33

# ---------- test that total returns 0 for empty cart without shipping ----------

def test_total_empty_cart():
    c = cart.Cart()
    assert c.total(member=True, coupon="SAVE20") == 0
