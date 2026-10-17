import pytest
import cart

# Helper to round floats for comparison
def r(v): return round(v,2)

class TestApplyDiscount:
    def test_basic(self):
        assert r(cart.apply_discount(200,15)) == 170.0
    def test_no_discount(self):
        assert r(cart.apply_discount(100,0)) == 100.0
    def test_full_discount(self):
        assert r(cart.apply_discount(123.456,100)) == 0.0
    def test_negative_price_raises(self):
        with pytest.raises(ValueError):
            cart.apply_discount(-10,5)
    def test_invalid_percent(self):
        for p in (-1,101):
            with pytest.raises(ValueError):
                cart.apply_discount(50,p)

class TestBulkDiscountPercent:
    @pytest.mark.parametrize("qty,expected",[
        (9,0),(10,5),(49,5),(50,10),(99,10),(100,15),(150,15)
    ])
    def test_values(self,qty,expected):
        assert cart.bulk_discount_percent(qty)==expected
    def test_non_positive_raises(self):
        for q in [0,-1,3.5]:
            with pytest.raises(ValueError):
                cart.bulk_discount_percent(q)

class TestShippingFee:
    def test_subtotal_below_threshold(self):
        assert r(cart.shipping_fee(45))==10.0
    def test_exact_threshold_no_fee(self):
        assert r(cart.shipping_fee(50))==0.0
    def test_member_discount(self):
        # 5% off shipping for members when over threshold
        assert r(cart.shipping_fee(200,member=True))==9.0

class TestCartOperations:
    def setup_method(self):
        self.c=cart.Cart()
    def test_add_and_items(self):
        self.c.add_item('apple',1.5,3)
        assert self.c.items() == [{'name':'apple','unit_price':1.5,'quantity':3}]
    def test_remove_partial(self):
        self.c.add_item('banana',2,5)
        self.c.remove_item('banana',2)
        assert self.c.items()==[{'name':'banana','unit_price':2,'quantity':3}]
    def test_remove_all(self):
        self.c.add_item('cherry',0.75,4)
        self.c.remove_item('cherry',4)
        assert self.c.items()==[]
    def test_subtotal_calculation(self):
        self.c.add_item('a',10,2);self.c.add_item('b',5,3)
        assert r(self.c.subtotal())==35.0
    def test_total_with_member_and_coupon(self):
        # setup items with bulk discounts
        self.c.add_item('item',20,120)  # should get 15% discount
        subtotal=self.c.subtotal()
        discounted=subtotal*(1-0.15)
        shipping=cart.shipping_fee(discounted,member=True)
        expected=discounted+shipping
        assert r(self.c.total(member=True,coupon=None))==round(expected,2)
    def test_total_with_coupon(self):
        self.c.add_item('item',50,1)
        # coupon gives flat 10 off after discounts
        total=self.c.total(coupon='SAVE10')
        assert isinstance(total,float)

# End of tests
