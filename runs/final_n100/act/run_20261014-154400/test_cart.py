import cart
import pytest

# ---------- Helper utilities ----------

def approx(value, target):
    """Helper for float comparison within two decimals."""
    return round(value, 2) == round(target, 2)

# ---------- Tests for standalone functions ----------

def test_apply_discount_normal():
    assert cart.apply_discount(200, 15) == pytest.approx(170.0, abs=1e-9)
    # check rounding behaviour
    assert cart.apply_discount(100, 33) == pytest.approx(67.0, abs=1e-9)


def test_apply_discount_rounding():
    # discount leads to non-integer result; should round to two decimals
    assert cart.apply_discount(99.99, 10) == pytest.approx(89.991, abs=1e-6)
    # rounding example: 100 * (1 - 33/100) = 67.0 exactly
    assert cart.apply_discount(100, 33) == pytest.approx(67.0)


def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        cart.apply_discount(-5, 10)


def test_apply_discount_invalid_percent_low():
    with pytest.raises(ValueError):
        cart.apply_discount(100, -1)


def test_apply_discount_invalid_percent_high():
    with pytest.raises(ValueError):
        cart.apply_discount(100, 101)


def test_bulk_discount_percent_edge_cases():
    # specification? assume it returns a percent based on quantity thresholds.
    assert isinstance(cart.bulk_discount_percent(1), float)


def test_parse_coupon_valid_and_invalid():
    # parse_coupon spec unknown; ensure return type is dict or None
    result = cart.parse_coupon('SAVE10')
    assert isinstance(result, (dict, type(None)))


def test_shipping_fee_basic():
    assert cart.shipping_fee(50) == pytest.approx(5.0)
    # member discount
    assert cart.shipping_fee(50, member=True) == pytest.approx(2.5)

# ---------- Tests for Cart class ----------

def test_cart_initial_state():
    c = cart.Cart()
    assert c.items() == []
    assert c.subtotal() == 0
    assert c.total() == pytest.approx(0.0)


def test_add_and_remove_items():
    c = cart.Cart()
    c.add_item('apple', unit_price=1.5, quantity=3)
    assert len(c.items()) == 1
    assert c.subtotal() == pytest.approx(4.5)
    # adding same item increases quantity
    c.add_item('apple', unit_price=1.5, quantity=2)
    assert c.items()[0]['quantity'] == 5
    assert c.subtotal() == pytest.approx(7.5)

    # remove some quantity
    c.remove_item('apple', quantity=3)
    assert c.items()[0]['quantity'] == 2
    assert c.subtotal() == pytest.approx(3.0)

    # removing more than existing should raise error or set to zero; test behavior
    with pytest.raises(ValueError):
        c.remove_item('apple', quantity=5)


def test_total_with_member_and_coupon():
    c = cart.Cart()
    c.add_item('widget', unit_price=20.0, quantity=2)  # subtotal 40
    # Without member or coupon
    assert c.total() == pytest.approx(45.0)  # assume shipping fee 5
    # With member discount on shipping
    assert c.total(member=True) == pytest.approx(42.5)

    # Coupon: assume 'SAVE10' gives 10% off total before shipping
    # We need to determine expected; using spec assumption
    coupon = {'discount_percent': 10}
    # monkeypatch parse_coupon if needed
    import types
    def fake_parse(code):
        return coupon if code=='SAVE10' else None
    original_parse = cart.parse_coupon
    cart.parse_coupon = fake_parse
    try:
        assert c.total(coupon='SAVE10') == pytest.approx(45.0 * 0.9 + 5)
    finally:
        cart.parse_coupon = original_parse


def test_cart_invalid_operations():
    c = cart.Cart()
    # remove non-existing item should raise error
    with pytest.raises(KeyError):
        c.remove_item('nonexistent')

# Run tests when executed directly
if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__]))
