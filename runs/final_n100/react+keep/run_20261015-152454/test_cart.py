import pytest
import cart

# ----------------------
# apply_discount tests
# ----------------------

def test_apply_discount_valid():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(100, 50) == 50.0

@pytest.mark.parametrize("price", [-1, -10.5])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 20)

@pytest.mark.parametrize("percent", [-5, 101, 150])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ----------------------------
# bulk_discount_percent tests
# ----------------------------

def test_bulk_discount_thresholds():
    assert cart.bulk_discount_percent(9) == 0
    # Expected 10 for quantity 50 according to spec
    assert cart.bulk_discount_percent(50) == 10, "Expected 10 for quantity 50"
    assert cart.bulk_discount_percent(51) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@pytest.mark.parametrize("quantity", [0, -5, 3.5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# -----------------------
# parse_coupon tests
# -----------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    # Spec says surrounding whitespace ignored, case-insensitive
    assert cart.parse_coupon("  SaVe50 ") == 50

@pytest.mark.parametrize("code", ["", "SAV10", "SAVE0", "SAVE51", "  SAVE10a  ", None])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ----------------------
# shipping_fee tests
# ----------------------

def test_shipping_fee_free_and_nonfree():
    assert cart.shipping_fee(1001) == 0
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(999) == 60

@pytest.mark.parametrize("subtotal", [-5, -1])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Member shipping half

def test_member_shipping_half():
    assert cart.shipping_fee(500, member=True) == 30.0
    assert cart.shipping_fee(1200, member=True) == 0

# -------------------
# Cart item methods
# -------------------

def test_cart_add_and_remove():
    c = cart.Cart()
    c.add_item("apple", 1.5, 2)
    assert c.items() == {"apple": 2}
    c.add_item("apple", 1.5, 3)
    assert c.items()["apple"] == 5
    with pytest.raises(ValueError):
        c.add_item("apple", 2.0)
    c.remove_item("apple", 4)
    assert c.items()["apple"] == 1
    # Removing the remaining quantity should delete the item
    c.remove_item("apple", 1)
    assert "apple" not in c.items()
    with pytest.raises(KeyError):
        c.remove_item("banana")

# -----------------------
# subtotal and total tests
# -----------------------

def test_cart_subtotal_discounts_and_rounding():
    c = cart.Cart()
    # 10 units at $100 -> bulk discount 5%
    c.add_item("widget", 100, 10)
    assert c.subtotal() == 950.00
    # 51 units at $200 -> bulk discount 10%
    c.add_item("gadget", 200, 51)
    widget_discount = cart.apply_discount(100 * 10, 5)
    gadget_discount = cart.apply_discount(200 * 51, 10)
    expected_total = round(widget_discount + gadget_discount, 2)
    assert c.subtotal() == expected_total

def test_cart_total_with_coupon_and_shipping():
    c = cart.Cart()
    # subtotal 1100 to trigger shipping after coupon
    c.add_item("expensive", 1000, 1)
    c.add_item("addon", 100, 1)
    assert c.subtotal() == 1100.00
    total = c.total(member=False, coupon="SAVE20")
    expected_amount_after_coupon = cart.apply_discount(1100, 20)
    expected_total = round(expected_amount_after_coupon + cart.shipping_fee(1100), 2)
    assert total == expected_total
    total_member = c.total(member=True, coupon="SAVE20")
    expected_shipping_member = cart.shipping_fee(1100) / 2
    expected_total_member = round(expected_amount_after_coupon + expected_shipping_member, 2)
    assert total_member == expected_total_member

# Empty cart should cost zero

def test_cart_empty_total():
    c = cart.Cart()
    assert c.total() == 0
    assert c.total(member=True) == 0
    assert c.total(coupon="SAVE10") == 0
