import pytest
import cart

# ---- apply_discount -----
@pytest.mark.parametrize("price,percent,result",[
    (200,15,170.0),
    (100,0,100.0),
    (50,50,25.0),
])
def test_apply_discount_valid(price,percent,result):
    assert cart.apply_discount(price,percent)==result

@pytest.mark.parametrize("price,percent",[
    (-10,20),
    (100,-5),
    (100,105),
])
def test_apply_discount_invalid(price,percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price,percent)

# ---- bulk_discount_percent -----
@pytest.mark.parametrize("quantity,result",[
    (9,0),
    (10,5),
    (49,5),
    (50,10),
    (99,10),
    (100,15),
    (200,15),
])
def test_bulk_discount_percent(quantity,result):
    assert cart.bulk_discount_percent(quantity)==result

@pytest.mark.parametrize("quantity",[-1,0,3.5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---- parse_coupon -----
valid_codes = {
    "SAVE10":10,
    "save25":25,
    "  SaVe50 ":50,
    "sAve1":1,
}
for code,exp in valid_codes.items():
    def _test(code=code, exp=exp):
        assert cart.parse_coupon(code)==exp
    globals()[f'test_parse_coupon_{code.strip()}'] = _test

invalid_codes=["",
    "SAVE0",  # below 1
    "SAVE51",# above 50
    "DISCOUNT10",
    "  SAVE-5 ",
    "SAVEXX",
]
for code in invalid_codes:
    def _test(code=code):
        with pytest.raises(ValueError):
            cart.parse_coupon(code)
    globals()[f'test_parse_coupon_invalid_{code.strip()}'] = _test

# ---- shipping_fee -----
@pytest.mark.parametrize("subtotal,member,result",[
    (0,False,60),
    (999.99,False,60),
    (1000,False,0),
    (1500,True,0),
    (500,True,30),
])
def test_shipping_fee(subtotal,member,result):
    assert cart.shipping_fee(subtotal,member)==result

@pytest.mark.parametrize("subtotal",[-1,-100.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Cart -----
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_empty_cart_totals(self):
        assert self.c.items()==[]
        assert self.c.subtotal()==0.0
        assert self.c.total()==0.0

    def test_add_item_and_subtotal(self):
        self.c.add_item('apple', 10, quantity=3)
        self.c.add_item('banana', 5)
        assert self.c.items()==[
            {'name':'apple','unit_price':10,'quantity':3},
            {'name':'banana','unit_price':5,'quantity':1}
        ]
        assert self.c.subtotal()==35.0

    def test_remove_item(self):
        self.c.add_item('x', 2, quantity=4)
        self.c.remove_item('x', quantity=2)
        assert self.c.items() == [{'name':'x','unit_price':2,'quantity':2}]
        # removing more than present removes the item
        self.c.remove_item('x', quantity=5)
        assert self.c.items()==[]

    def test_total_with_coupon_and_shipping(self):
        # 3 items of $100 -> subtotal 300, no bulk discount per spec (not applied in total)
        self.c.add_item('expensive', 100, quantity=3)
        # apply coupon SAVE10 (10% off)
        assert self.c.total(coupon='SAVE10') == round(300*0.9 + cart.shipping_fee(270),2)

    def test_total_member_shipping_half(self):
        self.c.add_item('item', 200, quantity=5)  # subtotal 1000 -> free shipping
        assert self.c.total(member=True)==0.0
        self.c = cart.Cart()
        self.c.add_item('small',10)
        expected = round(10 + cart.shipping_fee(10,member=True),2)
        assert self.c.total(member=True)==expected

    def test_invalid_coupon_in_total(self):
        self.c.add_item('p',1)
        with pytest.raises(ValueError):
            self.c.total(coupon='INVALID')
