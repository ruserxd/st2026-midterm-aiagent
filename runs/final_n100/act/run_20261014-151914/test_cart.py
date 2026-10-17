import cart
from pytest import approx

def test_apply_discount_valid():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 10) == 90.0
    # rounding example
    assert cart.apply_discount(99.999, 50) == 49.9995


def test_apply_discount_errors():
    import pytest
    with pytest.raises(ValueError):
        cart.apply_discount(-1, 10)
    with pytest.raises(ValueError):
        cart.apply_discount(100, -5)
    with pytest.raises(ValueError):
        cart.apply_discount(100, 105)


def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15


def test_bulk_discount_errors():
    import pytest
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-1)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)


def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon("  SaVe30 ") == 30


def test_parse_coupon_errors():
    import pytest
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVEX")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE5x")
    with pytest.raises(ValueError):
        cart.parse_coupon("50")


def test_shipping_fee():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(500, member=True) == 30


def test_shipping_fee_errors():
    import pytest
    with pytest.raises(ValueError):
        cart.shipping_fee(-1)

# Cart tests

def test_cart_add_and_items():
    c = cart.Cart()
    assert c.items() == {}
    c.add_item("apple", 100, 2)
    assert c.items() == {"apple": (100, 2)}


def test_cart_remove_item():
    c = cart.Cart()
    c.add_item("banana", 50, 5)
    c.remove_item("banana")
    assert c.items() == {"banana": (50, 4)}
    c.remove_item("banana", 4)
    assert c.items() == {}


def test_cart_subtotal():
    c = cart.Cart()
    c.add_item("item1", 20, 3)
    c.add_item("item2", 5, 10)
    assert c.subtotal() == 20*3 + 5*10


def test_cart_total_without_coupon():
    c = cart.Cart()
    c.add_item("widget", 1000, 1)
    # subtotal 1000 -> free shipping
    assert c.total() == approx(1000.0)
    c.add_item("gadget", 50, 2)  # total 1100
    assert c.total() == approx(1100.0)


def test_cart_total_with_coupon_and_member():
    c = cart.Cart()
    c.add_item("expensive", 500, 3)  # 1500 subtotal
    # coupon SAVE10 -> 15% discount
    assert c.total(coupon="SAVE10") == approx(1350.0)
    # member gets half shipping on 1350 (no free?) actually 1350>1000 so no shipping
    assert c.total(member=True, coupon="SAVE10") == approx(1350.0)
    c.add_item("cheapest", 10, 1)   # subtotal 1510 -> discount 151.5 => 1348.5
    assert c.total(coupon="SAVE10") == approx(1348.5)


def test_cart_total_errors():
    import pytest
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
