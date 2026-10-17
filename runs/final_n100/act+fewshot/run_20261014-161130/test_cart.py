import pytest
import cart

# Helper for rounding check
@ pytest.mark.parametrize("price,percent,result", [
    (200,15,170.0),
    (100,0,100.0),
    (100,100,0.0)
])
def test_apply_discount(price,percent,result):
    assert cart.apply_discount(price, percent) == result

# invalid values
@pytest.mark.parametrize("price,percent", [(-1,10),(50,-5),(50,150)])
def test_apply_discount_invalid(price,percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price,percent)

# bulk discount percentages
@pytest.mark.parametrize("qty,expected",[(9,0),(10,5),(49,5),(50,10),(99,10),(100,15)])
def test_bulk_discount(qty,expected):
    assert cart.bulk_discount_percent(qty)==expected

with pytest.raises(ValueError):
    cart.bulk_discount_percent(0)

# parse coupon
@pytest.mark.parametrize("code,result",[("SAVE10",10),("  save20 ",20),("SaVe5",5)])
def test_parse_coupon(code,result):
    assert cart.parse_coupon(code)==result

@pytest.mark.parametrize("code",["BAD10","SAVE0","SAVE51","SAVE-1",""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping fee
@pytest.mark.parametrize("subtotal,member,fee",[(999,False,60),(1000,False,0),(2000,True,0),(500,True,30)])
def test_shipping_fee(subtotal,member,fee):
    assert cart.shipping_fee(subtotal, member)==fee

with pytest.raises(ValueError):
    cart.shipping_fee(-10)

# Cart operations and totals
class TestCart:
    def setup_method(self):
        self.c=cart.Cart()

    def test_empty_cart_totals(self):
        assert self.c.items()=={}
        assert self.c.subtotal()==0
        assert self.c.total()==0
        assert self.c.total(member=True)==0

    def test_add_and_remove(self):
        self.c.add_item('apple',1,3)
        assert self.c.items()=='{\'apple\': 3}' if isinstance(self.c.items(),str) else self.c.items()=={'apple':3}
        self.c.remove_item('apple',2)
        assert self.c.items()=='{\'apple\': 1}' if isinstance(self.c.items(),str) else self.c.items()=={'apple':1}

    def test_subtotal_bulk_discount(self):
        # 10 apples at $1 each => bulk discount 5% -> line_total=10*1=10, discounted 9.5
        self.c.add_item('apple',1,10)
        assert self.c.subtotal()==9.5

    def test_coupon_and_shipping(self):
        # subtotal 50 with no bulk discount
        self.c.add_item('toy',10,5)   # 5 items $10 each -> 50, quantity<10 so no bulk
        # coupon SAVE10 gives 10% off: 45
        amount=self.c.total(coupon='SAVE10')
        # shipping_fee on subtotal(50)=60 (not member)
        assert amount==round(45+60,2)

    def test_member_shipping_and_no_coupon(self):
        self.c.add_item('book',200,1)  # subtotal 200
        total=self.c.total(member=True)
        # shipping on subtotal=60, member half=30
        assert total==round(200+30,2)
