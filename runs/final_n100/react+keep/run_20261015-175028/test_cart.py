import cart
import pytest

def round2(v): return round(v,2)

class TestParseCoupon:
    def test_valid_codes(self):
        for code in ["SAVE10", "save20", "SAve30"]:
            assert cart.parse_coupon(code) == int(code.strip()[4:])
    def test_invalid_codes(self):
        for code in ["SAVE0","SAVE51","DISCOUNT10","SAVEX",""]:
            with pytest.raises(ValueError):
                cart.parse_coupon(code)

class TestBulkDiscountPercent:
    def test_quantities(self):
        assert cart.bulk_discount_percent(9)==0
        assert cart.bulk_discount_percent(10)==5
        assert cart.bulk_discount_percent(49)==5
        assert cart.bulk_discount_percent(50)==10  # spec
        assert cart.bulk_discount_percent(99)==10
        assert cart.bulk_discount_percent(100)==15
    def test_invalid(self):
        for q in [0,-1,2.5]:
            with pytest.raises(ValueError):
                cart.bulk_discount_percent(q)

class TestShippingFee:
    def test_fee_cases(self):
        assert cart.shipping_fee(1000)==0
        assert cart.shipping_fee(1500)==0
        assert cart.shipping_fee(999.99)==60
        assert cart.shipping_fee(0)==60
        assert cart.shipping_fee(500)==60
    def test_member_half(self):
        assert cart.shipping_fee(50,member=True)==30
        assert cart.shipping_fee(800,member=True)==30
    def test_invalid_subtotal(self):
        for s in [-1,-100]:
            with pytest.raises(ValueError):
                cart.shipping_fee(s)

class TestApplyDiscount:
    def test_valid(self):
        assert cart.apply_discount(200,15)==170.0
        assert cart.apply_discount(100,10)==90.0
        assert cart.apply_discount(33.3333,5)==round2(33.3333*0.95)
    def test_invalid_params(self):
        with pytest.raises(ValueError):cart.apply_discount(-10,20)
        with pytest.raises(ValueError):cart.apply_discount(100,-1)
        with pytest.raises(ValueError):cart.apply_discount(100,101)

class TestCartOperations:
    def test_add_and_subtotal(self):
        c=cart.Cart();c.add_item("apple",1.0,quantity=5)
        assert round2(c.subtotal())==5.00
        c.add_item("banana",2.0,quantity=12)
        expected=12*2.0*0.95
        assert round2(c.subtotal())==round2(5+expected)
    def test_add_existing_same_price(self):
        c=cart.Cart();c.add_item("apple",1.0,quantity=3);c.add_item("apple",1.0,quantity=4)
        assert round2(c.subtotal())==7.00
    def test_add_existing_diff_price(self):
        c=cart.Cart();c.add_item("apple",1.0,quantity=3)
        with pytest.raises(ValueError):c.add_item("apple",2.0,quantity=1)
    def test_remove_and_total(self):
        c=cart.Cart();c.add_item("item",100,quantity=10)
        expected_subtotal=10*100*0.95
        shipping=60 if expected_subtotal<1000 else 0
        assert round2(c.total())==round2(expected_subtotal+shipping)
        total_coupon=c.total(coupon="SAVE10")
        discounted=cart.apply_discount(expected_subtotal,10)
        shipping2=cart.shipping_fee(discounted)
        assert round2(total_coupon)==round2(discounted+shipping2)
    def test_total_member(self):
        c=cart.Cart();c.add_item("item",200,quantity=4)  # subtotal 800
        subtotal=800
        assert round2(c.total(member=True))==round2(subtotal+(30 if subtotal<1000 else 0))
    def test_total_empty_cart(self):
        c=cart.Cart();assert c.total()==0
    def test_invalid_coupon_raises_value_error(self):
        c=cart.Cart();c.add_item("item",50,quantity=1)
        with pytest.raises(ValueError):c.total(coupon="BADCODE")
    def test_remove_item_quantity(self):
        c=cart.Cart();c.add_item("apple",3.0,quantity=5)
        c.remove_item("apple",quantity=2)
        assert round2(c.subtotal())==3*(5-2)
        c.remove_item("apple",quantity=3)
        assert len(c.items())==1 and list(c.items().values())[0]==0
        with pytest.raises(KeyError):c.remove_item("banana")
