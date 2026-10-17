import pytest
import cart
from math import isclose

def approx(a,b,tol=1e-9):
    return isclose(a,b,abs_tol=tol)

# ---------- apply_discount tests ----------
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
        (123.45, 20, 98.76),
    ],
)
def test_apply_discount(price,percent,result):
    assert cart.apply_discount(price,percent)==result

@pytest.mark.parametrize(
    "price,percent",
    [(-1,10),(100,-5),(100,105)],
)
def test_apply_discount_errors(price,percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price,percent)

# ---------- bulk_discount_percent tests ----------
@pytest.mark.parametrize(
    "quantity,result",
    [ (5,0),(10,5),(49,5),(50,10),(99,10),(100,15),(200,15) ],
)
def test_bulk_discount_percent(quantity,result):
    assert cart.bulk_discount_percent(quantity)==result

@pytest.mark.parametrize(
    "quantity",
    [0,-10,1.5],
)
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon tests ----------
valid_coupons={"SAVE10":10,"save20":20," SAVE5 ":5,"SaVe50":50}
@pytest.mark.parametrize("code,percent",valid_coupons.items())
def test_parse_coupon_valid(code,percent):
    assert cart.parse_coupon(code)==percent

invalid_coupons=["SAV10","SAVE0","SAVE51","DISCOUNT10","save-5","   "]
@pytest.mark.parametrize("code",invalid_coupons)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee tests ----------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [ (0,False,60),(500,True,30),(1000,False,0),(1500,True,0) ],
)
def test_shipping_fee(subtotal,member,expected):
    assert cart.shipping_fee(subtotal,member)==expected

@pytest.mark.parametrize("subtotal",[-1,-100])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart tests ----------
class TestCart:
    def setup_method(self):
        self.c=cart.Cart()
    def test_empty_cart_total(self):
        assert self.c.total()==0.0
    def test_add_and_subtotal(self):
        self.c.add_item("apple",100,quantity=3)
        self.c.add_item("banana",200)
        assert self.c.subtotal()==500.0
        items=self.c.items()
        assert {i["name"] for i in items}=={"apple","banana"}
    def test_remove_item(self):
        self.c.add_item("pear",150,quantity=4)
        self.c.remove_item("pear",quantity=2)
        assert self.c.items()[0]["quantity"]==2
        self.c.remove_item("pear",quantity=5)
        assert len(self.c.items())==0
    def test_total_without_coupon(self):
        self.c.add_item("item1",500,quantity=1)
        assert self.c.total()==560.0
    def test_total_with_member_discount_and_coupon(self):
        self.c.add_item("bulk",10,quantity=50)
        total=self.c.total(coupon="SAVE20")
        expected_after_coupon=cart.apply_discount(self.c.subtotal(),20)
        shipping=cart.shipping_fee(expected_after_coupon,member=False)
        assert approx(total,expected_after_coupon+shipping)
    def test_total_invalid_coupon(self):
        self.c.add_item("item",100)
        with pytest.raises(ValueError):
            self.c.total(coupon="BADCODE")
