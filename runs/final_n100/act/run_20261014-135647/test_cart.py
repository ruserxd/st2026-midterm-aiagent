import pytest
import cart

# --- apply_discount -------------------------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0


def test_apply_discount_rounding():
    # 100 * 33.333% = 66.6667 -> rounded to 2 decimals 66.67
    assert cart.apply_discount(100, 33.333) == 66.67


def test_apply_discount_zero_percent():
    assert cart.apply_discount(123.45, 0) == 123.45


def test_apply_discount_full_percent():
    assert cart.apply_discount(50, 100) == 0.0


def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        cart.apply_discount(-10, 20)


def test_apply_discount_invalid_percent_low():
    with pytest.raises(ValueError):
        cart.apply_discount(50, -5)


def test_apply_discount_invalid_percent_high():
    with pytest.raises(ValueError):
        cart.apply_discount(50, 105)

# --- bulk_discount_percent ------------------------------------------

def test_bulk_discount_percent_no_discount():
    assert cart.bulk_discount_percent(1) == 0


def test_bulk_discount_percent_ten():
    assert cart.bulk_discount_percent(10) == 5


def test_bulk_discount_percent_fifty():
    assert cart.bulk_discount_percent(50) == 10


def test_bulk_discount_percent_hundred():
    assert cart.bulk_discount_percent(100) == 15


def test_bulk_discount_percent_above_thresholds():
    assert cart.bulk_discount_percent(2000) == 15


def test_bulk_discount_percent_invalid_nonint():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(3.5)


def test_bulk_discount_percent_invalid_negative():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-10)

# --- parse_coupon ---------------------------------------------------

def test_parse_coupon_valid_uppercase():
    assert cart.parse_coupon("SAVE10") == 10


def test_parse_coupon_valid_lowercase_and_whitespace():
    assert cart.parse_coupon("  save25 ") == 25


def test_parse_coupon_edge_cases_min_max():
    assert cart.parse_coupon("save1") == 1
    assert cart.parse_coupon("SAVE50") == 50


def test_parse_coupon_invalid_format():
    with pytest.raises(ValueError):
        cart.parse_coupon("INVALID")


def test_parse_coupon_invalid_number_out_of_range():
    with pytest.raises(ValueError):
        cart.parse_coupon("save0")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE51")

# --- shipping_fee ---------------------------------------------------

def test_shipping_fee_free_threshold():
    assert cart.shipping_fee(1000) == 0


def test_shipping_fee_regular_non_member():
    assert cart.shipping_fee(500) == 60


def test_shipping_fee_member_half_fee():
    assert cart.shipping_fee(200, member=True) == 30


def test_shipping_fee_edge_subtotal_zero():
    assert cart.shipping_fee(0) == 60


def test_shipping_fee_invalid_negative():
    with pytest.raises(ValueError):
        cart.shipping_fee(-5)

# --- Cart class -----------------------------------------------------

def test_cart_add_and_items_and_subtotal():
    c = cart.Cart()
    c.add_item("apple", 1.0, quantity=3)
    c.add_item("banana", 0.5, quantity=2)
    assert c.items() == {"apple": 3, "banana": 2}
    # subtotal = 3*1.0 + 2*0.5 = 4.0
    assert c.subtotal() == 4.0


def test_cart_add_existing_item_increases_quantity_and_price_match():
    c = cart.Cart()
    c.add_item("apple", 1.0, quantity=3)
    c.add_item("apple", 1.0, quantity=2)
    assert c.items() == {"apple": 5}

    with pytest.raises(ValueError):
        # price mismatch
        c.add_item("apple", 1.5, quantity=1)


def test_cart_remove_partial_and_complete():
    c = cart.Cart()
    c.add_item("orange", 0.8, quantity=5)
    c.remove_item("orange", quantity=2)
    assert c.items() == {"orange": 3}
    c.remove_item("orange", quantity=3)
    assert "orange" not in c.items()


def test_cart_remove_nonexistent_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexist")


def test_cart_total_without_discounts_or_coupons_and_member_flag():
    c = cart.Cart()
    c.add_item("item", 200, quantity=4)   # subtotal 800
    total_no_fee = c.total(member=False)
    # shipping fee 60, no coupon
    assert total_no_fee == 860.0
    total_member = c.total(member=True)
    # member half shipping 30
    assert total_member == 830.0


def test_cart_total_with_coupon_and_bulk_discount():
    c = cart.Cart()
    # 120 units of product at $10 each => subtotal 1200
    c.add_item("widget", 10, quantity=120)
    # bulk discount percent for 120 is 15%
    # apply discount: 1200 * 0.85 = 1020
    # shipping free because subtotal >=1000 before discount? 
    # total() uses subtotal before discounts to compute shipping.
    # So shipping fee should be 0.
    total = c.total(coupon="save20", member=False)
    # coupon 20% -> 1020 * 0.8 = 816
    assert pytest.approx(total, rel=1e-9) == 816.0

# end of tests
