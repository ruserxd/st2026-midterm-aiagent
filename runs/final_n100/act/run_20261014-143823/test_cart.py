import pytest
from cart import Cart, parse_coupon

def make_cart(**items):
    c = Cart()
    for name,(price,qty) in items.items():
        c.add_item(name, price, qty)
    return c

class TestCartSubtotal:
    def test_empty(self): assert Cart().subtotal()==0
    def test_single(self):
        c=make_cart(a=(1.00,3))
        assert c.subtotal()==3.00
    def test_multiple(self):
        c=make_cart(x=(2.5,2),y=(1.25,4))
        expected=2*2.5+4*1.25
        assert c.subtotal()==expected

class TestCartTotal:
    def test_empty_total(self): assert Cart().total()==0
    def test_no_coupon(self):
        c=make_cart(item=(10,1))
        total=c.total()
        assert total>=c.subtotal()
    def test_coupon_reduction_and_shipping(self):
        c=make_cart(prod=(20,2))  # subtotal 40
        coupon="SAVE10"
        percent=parse_coupon(coupon)
        discounted=40*(1-percent/100)
        shipping=c.shipping_fee(discounted) if hasattr(c,'shipping_fee') else 0
        expected_total=round(discounted+shipping,2)
        assert c.total(coupon=coupon)==pytest.approx(expected_total)
    def test_invalid_coupon_raises(self):
        c=make_cart(item=(5,1))
        with pytest.raises(ValueError):
            c.total(coupon="UNKNOWN")
    def test_member_shipping_discount(self):
        c=make_cart(p=(30,1))
        non=c.total(member=False)
        mem=c.total(member=True)
        assert mem<=non

class TestParseCoupon:
    def test_valid_code_returns_percentage(self):
        code="SAVE20"
        percent=parse_coupon(code)
        assert isinstance(percent,(int,float))
        assert 1<=percent<=50
    def test_non_string_raises_value_error(self):
        with pytest.raises(ValueError):
            parse_coupon(123)
