import cart
import pytest

# Helper to compare floats
from math import isclose

def approx(a,b):
    return isclose(a,b,rel_tol=1e-9,abs_tol=0.01)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize("qty,expected", [
    (5,0),
    (10,5),
    (15,5),
    (50,10),
    (55,10),
    (100,15),
    (150,15)
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty)==expected

@pytest.mark.parametrize("qty", [0,-1,3.5])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- apply_discount ----------
@pytest.mark.parametrize("price,percent,result", [
    (200,15,170.0),
    (100,10,90.0),
    (50,0,50.0),
    (0,100,0.0)
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price,percent)==result

@pytest.mark.parametrize("price", [-1,-0.01])
def test_apply_discount_invalid_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price,10)

@pytest.mark.parametrize("percent", [ -5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100,percent)

# ---------- parse_coupon ----------
@pytest.mark.parametrize("code,result", [
    ("SAVE10",10),
    ("save20 ",20),
    ("  SaVe30",30),
])
def test_parse_coupon_valid(code,result):
    assert cart.parse_coupon(code)==result

@pytest.mark.parametrize("code", [
    "SAVExx",
    "SAVE0",
    "SAVE51",
    "10SAVE",
    "" ,
    "   ",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize("subtotal,member,expected", [
    (0,False,60),
    (99.99,False,60),
    (1000,False,0),
    (1500,True,0),
    (500,True,30)
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal,member)==expected

@pytest.mark.parametrize("subtotal", [-1,-100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class behaviour ----------
class TestCart:
    def setup_method(self):
        self.c=cart.Cart()

    def test_empty_cart_values(self):
        assert self.c.items()==[]
        assert self.c.subtotal()==0.0
        assert self.c.total()==0.0

    def test_add_and_remove_items(self):
        self.c.add_item("apple", 1.00, quantity=5)
        self.c.add_item("banana", 0.50, quantity=2)
        # subtotal: apples 5*1.0=5 (no bulk), bananas 2*0.5=1 -> total 6
        assert approx(self.c.subtotal(),6.0)
        self.c.remove_item("apple", quantity=3)  # left 2 apples
        # new subtotal: 2*1=2 + 1 =3
        assert approx(self.c.subtotal(),3.0)
        # remove more than present removes all
        self.c.remove_item("banana")
        assert "banana" not in [i['name'] for i in self.c.items()]

    def test_bulk_discount_in_subtotal(self):
        # 12 units -> bulk discount 5%
        self.c.add_item("widget", 10.0, quantity=12)
        expected = cart.apply_discount(120.0,5)  # 120 -5% =114
        assert approx(self.c.subtotal(),expected)

    def test_total_with_coupon_and_member(self):
        self.c.add_item("prod", 200.0, quantity=1)
        # subtotal 200
        total_without = cart.shipping_fee(200) + 200  # shipping 60
        assert approx(self.c.total(), total_without)
        # with coupon SAVE10 -> 180 before shipping, shipping for 180 is still 60
        expected = cart.apply_discount(200,10)+cart.shipping_fee(cart.apply_discount(200,10))
        assert approx(self.c.total(coupon="SAVE10"),expected)
        # member discount on shipping: subtotal 200 -> 60/2=30
        total_member = 200+30
        assert approx(self.c.total(member=True),total_member)

    def test_total_invalid_coupon(self):
        with pytest.raises(ValueError):
            self.c.total(coupon="invalid")
