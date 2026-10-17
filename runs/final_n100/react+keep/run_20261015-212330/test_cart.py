import pytest
import cart

# helper to compare floats with round

def approx(x, y):
    return pytest.approx(round(y,2), rel=1e-12)

class TestFunctions:
    def test_apply_discount_valid(self):
        assert cart.apply_discount(200,15)==170.0
        assert cart.apply_discount(100,0)==100.0
        assert cart.apply_discount(50,100)==0.0

    def test_apply_discount_errors(self):
        with pytest.raises(ValueError):
            cart.apply_discount(-10, 10)
        with pytest.raises(ValueError):
            cart.apply_discount(10, -1)
        with pytest.raises(ValueError):
            cart.apply_discount(10, 101)

    def test_bulk_discount_percent(self):
        assert cart.bulk_discount_percent(5)==0
        assert cart.bulk_discount_percent(10)==5
        assert cart.bulk_discount_percent(25)==10
        assert cart.bulk_discount_percent(120)==15

    def test_bulk_discount_percent_error(self):
        with pytest.raises(ValueError):
            cart.bulk_discount_percent(-1)
        with pytest.raises(ValueError):
            cart.bulk_discount_percent(0.5)  # not int

    def test_parse_coupon_valid(self):
        assert cart.parse_coupon("SAVE10")==10
        assert cart.parse_coupon("save20 ")==20
        assert cart.parse_coupon(" SAVE30")==30

    def test_parse_coupon_error(self):
        with pytest.raises(ValueError):
            cart.parse_coupon("DISCOUNT10")
        with pytest.raises(ValueError):
            cart.parse_coupon("SAVE0")
        with pytest.raises(ValueError):
            cart.parse_coupon("SAVE51")

    def test_shipping_fee(self):
        assert cart.shipping_fee(1200)==0
        assert cart.shipping_fee(999)==60
        assert cart.shipping_fee(500, member=True)==30

class TestCart:
    def test_add_and_items(self):
        c=cart.Cart()
        c.add_item('apple', 1.5)
        assert c.items()=={'apple':1}
        c.add_item('banana',2.0,3)
        assert c.items()=={'apple':1,'banana':3}
        # adding existing increases quantity
        c.add_item('apple',1.5,4)
        assert c.items()['apple']==5

    def test_add_errors(self):
        c=cart.Cart()
        with pytest.raises(ValueError):
            c.add_item('x', -1)
        with pytest.raises(ValueError):
            c.add_item('y',1,0)
        c.add_item('z',2)
        with pytest.raises(ValueError):
            c.add_item('z',3)  # price mismatch

    def test_remove(self):
        c=cart.Cart()
        c.add_item('x',5,5)
        c.remove_item('x',2)
        assert c.items()['x']==3
        c.remove_item('x',3)
        assert 'x' not in c.items()
        with pytest.raises(KeyError):
            c.remove_item('x')

    def test_subtotal(self):
        c=cart.Cart()
        c.add_item('item',100,10)  # bulk discount 5%
        assert c.subtotal()==95.0
        c.add_item('item2',200,50)
        # subtotal = 100*10*0.95 + 200*50*0.9
        expected=100*10*0.95+200*50*0.9
        assert c.subtotal()==round(expected,2)

    def test_total_no_coupon_member(self):
        c=cart.Cart()
        c.add_item('i',100,5)  # no bulk discount
        # subtotal = 500
        # member shipping half: 30 (since <1000)
        assert c.total(member=True)==530.0
        assert c.total(member=False)==560.0

    def test_total_with_coupon(self):
        c=cart.Cart()
        c.add_item('i',200,5)  # subtotal 1000 -> free shipping
        # apply coupon 20%: amount 800; shipping fee computed on subtotal (1000) -> 0
        assert c.total(coupon='SAVE20')==800.0

    def test_total_empty_cart(self):
        c=cart.Cart()
        assert c.total()==0
        assert c.total(member=True)==0

# Detect the subtle bug: shipping_fee should be based on amount after coupon,
# but current implementation uses subtotal again.
    def test_bug_shipping_after_coupon(self):
        c=cart.Cart()
        c.add_item('i',200,5)  # subtotal 1000
        # With a non free shipping scenario: use quantity that gives lower subtotal
        c._lines.clear(); c.add_item('i',50,3)  # subtotal 150 <1000, shipping 60
        amount_before = c.subtotal()
        total_with_coupon = c.total(coupon='SAVE20')
        # Expected amount after discount: 80% of subtotal + shipping(60)
        expected = round(amount_before*0.8+60,2)
        assert total_with_coupon==expected
