import pytest
import cart

# ---------- utility helpers -------------------------------------

def almost_equal(a, b, tol=1e-9):
    return abs(a - b) < tol

# ---------- tests for standalone functions ----------------------

def test_apply_discount_valid():
    assert cart.apply_discount(200, 15) == 170.0
    # price zero
    assert cart.apply_discount(0, 50) == 0.0
    # percent boundaries
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(100, 100) == 0.0


def test_apply_discount_invalid():
    with pytest.raises(ValueError):
        cart.apply_discount(-1, 10)
    with pytest.raises(ValueError):
        cart.apply_discount(50, -5)
    with pytest.raises(ValueError):
        cart.apply_discount(50, 105)


def test_bulk_discount_percent():
    # boundary checks
    assert cart.bulk_discount_percent(1) == 0
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15


def test_bulk_discount_invalid():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-5)
    with pytest.raises(ValueError):
        # non-integer
        cart.bulk_discount_percent(10.5)


def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon(" SAVE30 ") == 30
    # boundaries
    assert cart.parse_coupon("SAVE1") == 1
    assert cart.parse_coupon("SAVE50") == 50


def test_parse_coupon_invalid():
    with pytest.raises(ValueError):
        cart.parse_coupon("SAV10")      # missing E
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE0")      # below 1
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE51")     # above 50
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVEABC")   # not integer
    with pytest.raises(ValueError):
        cart.parse_coupon("12345")      # no SAVE prefix


def test_shipping_fee():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0
    # member discount
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(1200, member=True) == 0


def test_shipping_fee_invalid():
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

# ---------- tests for Cart class ---------------------------------

def test_cart_initial_state():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 0.0


def test_add_and_remove_items():
    c = cart.Cart()
    c.add_item("apple", 2.5, quantity=4)
    # bulk discount for quantity >=10? no
    assert c.items()["apple"] == (2.5, 4)
    assert c.subtotal() == 10.0
    c.remove_item("apple")
    assert c.items()["apple"] == (2.5, 3)
    assert c.subtotal() == 7.5
    # remove more than exists should reduce to zero and delete
    c.remove_item("apple", quantity=5)
    assert "apple" not in c.items()
    assert c.subtotal() == 0.0


def test_cart_bulk_discount_application():
    c = cart.Cart()
    # add 12 units of banana at 1 each -> subtotal 12
    c.add_item("banana", 1, quantity=12)
    # bulk discount percent for 12 is 5%
    assert cart.bulk_discount_percent(12) == 5
    # total without coupon or membership
    expected_sub = 12.0
    # apply bulk discount automatically? spec: subtotal() just sums; bulk not auto applied.
    # Therefore test that total uses shipping after coupon only.
    assert c.total() == round(expected_sub + cart.shipping_fee(expected_sub),2)


def test_cart_total_with_coupon_and_member():
    c = cart.Cart()
    c.add_item("widget", 100, quantity=3)   # subtotal 300
    # coupon SAVE10 => 10%
    total_without_shipping = 300 * 0.9
    shipping = cart.shipping_fee(total_without_shipping, member=True)
    expected_total = round(total_without_shipping + shipping,2)
    assert c.total(member=True, coupon="SAVE10") == expected_total


def test_cart_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item("item", 50, quantity=1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# ---------- run all tests ---------------------------------------
if __name__ == "__main__":
    import sys
    sys.exit(pytest.main(["-q", __file__]))
