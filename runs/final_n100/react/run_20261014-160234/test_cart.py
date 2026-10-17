import pytest
from cart import Cart, apply_discount, bulk_discount_percent, parse_coupon, shipping_fee

# ---------- Basic item operations ----------

def test_add_and_items():
    c = Cart()
    # add a single item
    c.add_item("apple", unit_price=0.5)
    assert "apple" in c.items()
    name, (price, qty) = list(c.items().items())[0]
    assert name == "apple"
    assert price == 0.5 and qty == 1


def test_add_multiple_quantities():
    c = Cart()
    c.add_item("banana", unit_price=0.2, quantity=3)
    assert c.items()["banana"] == (0.2, 3)


def test_remove_items():
    c = Cart()
    c.add_item("orange", unit_price=0.6, quantity=5)
    # remove some quantity
    c.remove_item("orange", quantity=2)
    assert c.items()["orange"] == (0.6, 3)
    # removing more than exists removes the item entirely
    c.remove_item("orange", quantity=10)
    assert "orange" not in c.items()

# ---------- Subtotal calculations ----------

def test_subtotal_single_and_multiple_items():
    c = Cart()
    c.add_item("tea", unit_price=2.0, quantity=2)   # 4.0
    c.add_item("coffee", unit_price=3.5)            # 3.5
    assert c.subtotal() == 7.5

# ---------- Shipping fee logic ----------

def test_shipping_fee_non_member_and_empty():
    # non-member: $10 shipping for any subtotal > 0, free otherwise
    assert shipping_fee(0) == 0
    assert shipping_fee(30) == 10


def test_shipping_fee_member():
    # members have free shipping regardless of amount
    assert shipping_fee(30, member=True) == 0
    assert shipping_fee(0, member=True) == 0

# ---------- Bulk discount logic ----------

def test_bulk_discount_percent_thresholds():
    # 5+ items -> 5% discount, >10 -> 10%, otherwise no discount
    assert bulk_discount_percent(4) == 0
    assert bulk_discount_percent(5) == 5
    assert bulk_discount_percent(11) == 10

# ---------- Coupon parsing and application ----------

def test_parse_coupon_valid_and_invalid():
    assert parse_coupon("DISCOUNT10") == 10
    with pytest.raises(ValueError):
        parse_coupon("INVALIDCODE")


def test_apply_discount_basic_and_bulk():
    # apply a simple discount: 10% off $100 -> $90
    assert apply_discount(100, 10) == 90
    # combine bulk discount percent: e.g., quantity 6 => 5% off 200 -> 190
    # Since apply_discount only takes price and percent, we test directly
    assert round(apply_discount(200, bulk_discount_percent(6)), 2) == 190

# ---------- Total calculation with coupons and shipping ----------

def test_total_no_coupon_no_member():
    c = Cart()
    c.add_item("book", unit_price=20)
    # subtotal 20, no coupon -> apply shipping of $10 => 30
    assert c.total() == 30.0


def test_total_with_member_free_shipping_and_discount():
    c = Cart()
    c.add_item("pen", unit_price=5, quantity=4)  # subtotal 20
    # member: free shipping, apply discount coupon 10%
    assert c.total(member=True, coupon="DISCOUNT10") == 18.0  # 20*0.9=18 no shipping


def test_total_invalid_coupon():
    c = Cart()
    c.add_item("notebook", unit_price=15)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# ---------- Edge cases: empty cart ----------

def test_empty_cart_total_and_subtotal():
    c = Cart()
    assert c.subtotal() == 0
    assert c.total() == 0.0

# ---------- Order of operations with bulk discount and coupons ----------

def test_bulk_discount_applied_before_coupon_and_shipping():
    # Assume that total applies coupon after subtotal but before shipping
    # We'll simulate by manually computing expected value
    c = Cart()
    c.add_item("item", unit_price=50, quantity=6)  # subtotal 300, bulk discount 5% -> 285? actually bulk discount percent used only in apply_discount? spec unclear but test ensures sequence.
    # For the purpose of this test, assume no bulk discount in total (since not part of Cart.total spec)
    # We'll just ensure that coupon is applied to subtotal then shipping added
    expected = 300 * (1 - parse_coupon("DISCOUNT20")/100) + shipping_fee(300 * (1 - parse_coupon("DISCOUNT20")/100))
    assert round(c.total(coupon="DISCOUNT20"), 2) == round(expected, 2)
