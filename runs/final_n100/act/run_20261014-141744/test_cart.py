import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# Helper function to compare floats with tolerance

def approx_equal(a,b,eps=1e-6):
    return abs(a-b) < eps

# ---------- apply_discount tests ----------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(50, 100) == 0.0


def test_apply_discount_rounding_and_zeros():
    # ensure rounding to 2 decimals
    assert apply_discount(123.456, 10) == round(123.456 * 0.9, 2)
    # zero price stays zero
    assert apply_discount(0, 50) == 0.0


def test_apply_discount_errors():
    with pytest.raises(ValueError):
        apply_discount(-5, 10)
    with pytest.raises(ValueError):
        apply_discount(100, -1)
    with pytest.raises(ValueError):
        apply_discount(100, 101)

# ---------- bulk_discount_percent tests ----------

def test_bulk_discount_percent_basic():
    # No discount for small quantity
    assert bulk_discount_percent(0) == 0.0
    assert bulk_discount_percent(1) == 0.0
    # 5% for 10-19 items
    assert bulk_discount_percent(10) == 5.0
    assert bulk_discount_percent(15) == 5.0
    # 10% for 20-49 items
    assert bulk_discount_percent(20) == 10.0
    assert bulk_discount_percent(35) == 10.0
    # 15% for 50+ items
    assert bulk_discount_percent(50) == 15.0
    assert bulk_discount_percent(75) == 15.0

# ---------- parse_coupon tests ----------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10.0
    assert parse_coupon("  Discount5 ") == 5.0


def test_parse_coupon_invalid_format():
    with pytest.raises(ValueError):
        parse_coupon("100")   # no alphabetic prefix
    with pytest.raises(ValueError):
        parse_coupon("SAVE-10") # invalid characters
    with pytest.raises(ValueError):
        parse_coupon(123)  # non-string

# ---------- shipping_fee tests ----------

def test_shipping_fee_basic():
    assert shipping_fee(0) == 5.99
    assert shipping_fee(100) == 4.49
    assert shipping_fee(200) == 0.0


def test_shipping_fee_member_discount():
    # member discount applies a flat $1 reduction to fee, min 0
    assert shipping_fee(0, member=True) == max(5.99-1, 0)
    assert shipping_fee(100, member=True) == max(4.49-1, 0)
    assert shipping_fee(200, member=True) == max(0-1, 0)

# ---------- Cart class tests ----------

def test_cart_initially_empty():
    c = Cart()
    assert c.items() == []
    assert c.subtotal() == 0.0
    assert c.total() == 5.99  # shipping fee for empty cart


def test_cart_add_and_remove_items():
    c = Cart()
    c.add_item("apple", 1.0, quantity=3)
    c.add_item("banana", 0.5)
    assert c.items() == [(
        "apple", 1.0, 3
    ), (
        "banana", 0.5, 1
    )]
    assert c.subtotal() == approx_equal(3*1.0 + 0.5, 3.5)
    # remove one apple
    c.remove_item("apple")
    assert any(name=="apple" and q==2 for name, _, q in c.items())
    # remove banana completely
    c.remove_item("banana", quantity=1)
    assert not any(name=="banana" for name,_,_ in c.items())


def test_cart_total_with_member_and_coupon():
    c = Cart()
    c.add_item("widget", 20.0, quantity=5)   # subtotal 100
    total_no_discount = c.total(member=False)
    assert approx_equal(total_no_discount, 100 + shipping_fee(100))

    # member discount applied to fee only
    total_member = c.total(member=True)
    expected_fee = max(shipping_fee(100)-1,0)
    assert approx_equal(total_member, 100 + expected_fee)

    # apply coupon of 10% off subtotal
    total_coupon = c.total(coupon="SAVE10")
    discounted_subtotal = apply_discount(100, 10.0)
    assert approx_equal(total_coupon, discounted_subtotal + shipping_fee(discounted_subtotal))

    # combined member and coupon
    total_both = c.total(member=True, coupon="SAVE5")
    discounted = apply_discount(100,5.0)
    fee_with_member = max(shipping_fee(discounted)-1,0)
    assert approx_equal(total_both, discounted + fee_with_member)
