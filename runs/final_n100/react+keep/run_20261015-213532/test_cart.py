import pytest
import cart

# Test apply_discount

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0


def test_apply_discount_rounding():
    # round to two decimals
    assert cart.apply_discount(99.99, 1) == round(99.99 * 0.99, 2)


def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        cart.apply_discount(-10, 20)


def test_apply_discount_invalid_percent_low():
    with pytest.raises(ValueError):
        cart.apply_discount(100, -5)


def test_apply_discount_invalid_percent_high():
    with pytest.raises(ValueError):
        cart.apply_discount(100, 120)

# Test bulk_discount_percent

def test_bulk_discount_percent_zero_and_small():
    assert cart.bulk_discount_percent(1) == 0
    assert cart.bulk_discount_percent(9) == 0


def test_bulk_discount_percent_boundaries():
    # Boundary values per specification
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15


def test_bulk_discount_invalid_quantity():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-5)

# Test parse_coupon

def test_parse_coupon_valid_cases():
    # Leading/trailing whitespace and case-insensitivity are allowed
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon("  SaVe30   ") == 30


def test_parse_coupon_invalid_format():
    with pytest.raises(ValueError):
        cart.parse_coupon("SAV10")  # missing 'E'
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE-5")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE0")   # below min
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE51")  # above max
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE")   # no number
    with pytest.raises(ValueError):
        cart.parse_coupon(123)       # wrong type

# Test shipping_fee

def test_shipping_fee_standard():
    assert cart.shipping_fee(999.99, member=False) == 60
    assert cart.shipping_fee(500, member=True) == 30


def test_shipping_fee_free():
    assert cart.shipping_fee(1000, member=False) == 0
    assert cart.shipping_fee(2000, member=True) == 0


def test_shipping_fee_invalid_subtotal():
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

# Test Cart total calculation

def test_cart_total_empty_and_no_coupon_non_member():
    c = cart.Cart()
    assert c.total(member=False, coupon=None) == 0


def test_cart_total_with_items_no_coupon_non_member():
    c = cart.Cart()
    c.add_item("apple", 100.00, quantity=3)
    # subtotal 300; shipping 60 = total 360
    assert c.total(member=False, coupon=None) == 360


def test_cart_total_with_items_no_coupon_member():
    c = cart.Cart()
    c.add_item("banana", 50.00, quantity=2)
    # subtotal 100; shipping 30 = total 130
    assert c.total(member=True, coupon=None) == 130


def test_cart_total_with_coupon_non_member():
    c = cart.Cart()
    c.add_item("tshirt", 200.00)
    # subtotal 200; apply SAVE10 =>180; shipping 60 =>240
    assert c.total(member=False, coupon="SAVE10") == 240


def test_cart_total_with_coupon_member():
    c = cart.Cart()
    c.add_item("jacket", 800.00)
    # subtotal 800; apply SAVE5 =>760; shipping 30 =>790
    assert c.total(member=True, coupon="save5") == 790


def test_cart_total_coupon_invalid_raises():
    c = cart.Cart()
    c.add_item("item", 100)
    with pytest.raises(ValueError):
        c.total(member=False, coupon="BADCODE")

# Test rounding in total

def test_cart_total_rounding_issue():
    # subtotal 33.33; apply SAVE7 =>30.99; shipping 60 =>90.99
    c = cart.Cart()
    c.add_item("item", 33.33)
    assert c.total(member=False, coupon="SAVE7") == round(30.99 + 60, 2)
