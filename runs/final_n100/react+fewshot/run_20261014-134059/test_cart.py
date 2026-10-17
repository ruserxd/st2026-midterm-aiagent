import pytest
import cart

# ---------- utility helper functions for expected calculations ----------

def bulk_discount_for(q):
    if q >= 100:
        return 15
    if q >= 50:
        return 10
    if q >= 10:
        return 5
    return 0

# ----- apply_discount ---------------------------------------------------

test_cases_apply = [
    (200, 15, 170.00),
    (100, 0, 100.00),
    (50, 25, 37.50),
]

@pytest.mark.parametrize("price,percent,result", test_cases_apply)
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# test edge cases for validation errors
def test_apply_discount_errors():
    with pytest.raises(ValueError):
        cart.apply_discount(-1, 10)
    with pytest.raises(ValueError):
        cart.apply_discount(100, -5)
    with pytest.raises(ValueError):
        cart.apply_discount(100, 110)

# ----- bulk_discount_percent --------------------------------------------

test_cases_bulk = [
    (1, 0),
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
]

@pytest.mark.parametrize("q,expected", test_cases_bulk)
def test_bulk_discount_percent(q, expected):
    assert cart.bulk_discount_percent(q) == expected

# validate errors for non‑positive quantity
def test_bulk_discount_errors():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-5)

# ----- parse_coupon -----------------------------------------------------

def test_parse_coupon_valid():
    valid_coupons = ["SAVE10", "save25", "  SaVe50 "]
    for code in valid_coupons:
        expected = int(code.strip().upper()[4:])
        assert cart.parse_coupon(code) == expected

def test_parse_coupon_invalid():
    invalid_codes = ["SAV5", "10SAVE", "WRONG", "save51", ""]
    for code in invalid_codes:
        with pytest.raises(ValueError):
            cart.parse_coupon(code)

# ----- shipping_fee ------------------------------------------------------

def test_shipping_fee():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(500) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1200) == 0
    # members pay half
    assert cart.shipping_fee(200, member=True) == 30
    assert cart.shipping_fee(1500, member=True) == 0

    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

# ----- Cart class -------------------------------------------------------

def test_cart_add_and_items():
    c = cart.Cart()
    assert c.items() == {}
    c.add_item("apple", 1.00, 3)
    assert c.items() == {"apple": 3}
    # add same item increases quantity
    c.add_item("apple", 1.00, 2)
    assert c.items() == {"apple": 5}
    # adding new item
    c.add_item("banana", 0.50, 4)
    assert c.items() == {"apple": 5, "banana": 4}


def test_cart_add_errors():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("orange", -1, 2)
    with pytest.raises(ValueError):
        c.add_item("orange", 1.5, 0)
    # mixing unit price
    c.add_item("pear", 2.0, 1)
    with pytest.raises(ValueError):
        c.add_item("pear", 3.0, 1)


def test_cart_remove_and_items():
    c = cart.Cart()
    c.add_item("mango", 1.5, 4)
    c.remove_item("mango", 2)
    assert c.items() == {"mango": 2}
    # remove more than existing
    c.remove_item("mango", 3)
    assert c.items() == {}
    with pytest.raises(KeyError):
        c.remove_item("nonexistent", 1)


def test_cart_subtotal():
    c = cart.Cart()
    # No items -> 0.00
    assert c.subtotal() == 0
    c.add_item("itemA", 10, 5)   # bulk discount 5%
    # expected: 10*5=50 reduced by 5% = 47.5
    assert c.subtotal() == 47.50
    c.add_item("itemB", 20, 12)  # bulk discount 5%
    # itemB subtotal: 240 *0.95 = 228
    # total expected: 47.5 + 228 = 275.5 rounded to 2 decimals
    assert c.subtotal() == 275.50


def test_cart_total_no_coupons():
    c = cart.Cart()
    # Empty cart -> 0 (no shipping)
    assert c.total() == 0
    # With items <1000 subtotal, member flag toggles shipping fee
    c.add_item("gadget", 300, 1)  # no bulk discount
    # subtotal = 300, after coupon none -> 300, shipping non‑member 60 = total 360
    assert c.total() == 360.00
    # member gets half shipping
    assert c.total(member=True) == 330.00


def test_cart_total_with_coupons_and_shipping():
    c = cart.Cart()
    c.add_item("prod", 200, 6)   # bulk discount 5% -> subtotal 1200*0.95=1140
    # no shipping because >=1000 after coupon? Shipping is based on amount AFTER coupon.
    # Here subtotal after coupon is 1140 which is >=1000 - free shipping.
    assert c.total() == 1140.00
    # Add a coupon SAVE10 (10% off)
    total_with_coupon = cart.apply_discount(1140, 10)  # 1026.0
    assert c.total(coupon="SAVE10") == total_with_coupon
    # Verify rounding to two decimals
    assert isinstance(c.total(), float)

# ---- verify coupon parsing within Cart.total error handling ----

def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("item", 100, 1)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
