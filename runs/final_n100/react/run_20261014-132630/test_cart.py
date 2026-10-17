import cart

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save25 ") == 25


def test_parse_coupon_invalid():
    import pytest
    with pytest.raises(ValueError):
        cart.parse_coupon("INVALID")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE0")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE51")


def test_apply_discount():
    assert cart.apply_discount(200, 15) == 170.0
    import pytest
    with pytest.raises(ValueError):
        cart.apply_discount(-1, 10)
    with pytest.raises(ValueError):
        cart.apply_discount(100, -5)
    with pytest.raises(ValueError):
        cart.apply_discount(100, 150)


def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(100) == 15
    import pytest
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-5)


def test_shipping_fee():
    assert cart.shipping_fee(500, member=False) == 60
    assert cart.shipping_fee(2000, member=True) == 0
    import pytest
    with pytest.raises(ValueError):
        cart.shipping_fee(-10, member=False)


def test_cart_total_no_coupon():
    c = cart.Cart()
    c.add_item("item1", 100, quantity=2)  # subtotal 200
    assert c.total(member=False) == 260.0  # shipping 60
    assert c.total(member=True) == 230.0   # shipping 30


def test_cart_total_with_coupon():
    c = cart.Cart()
    c.add_item("item1", 100, quantity=2)
    # subtotal 200 -> apply coupon SAVE10 => 180
    assert c.total(member=False, coupon="SAVE10") == 240.0  # shipping 60


def test_cart_empty():
    c = cart.Cart()
    assert c.total() == 0
