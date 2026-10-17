import cart
import pytest

def test_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0


def test_shipping_fee_non_member_and_threshold():
    assert cart.shipping_fee(500) == 60
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(1200) == 0


def test_coupon_parsing_and_application():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.apply_discount(200, cart.parse_coupon("SAVE10")) == 180
    with pytest.raises(ValueError):
        cart.parse_coupon("INVALID")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE0")


def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("item", 100.0, quantity=1)
    assert pytest.approx(c.total(coupon="SAVE10")) == 150


def test_member_free_shipping():
    c = cart.Cart()
    c.add_item("expensive", 100.0)
    assert pytest.approx(c.total(member=True)) == 130
