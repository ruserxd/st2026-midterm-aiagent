import pytest
import cart

# Helper for floats equality with round

def assert_close(a, b):
    assert round(a, 2) == round(b, 2)

# apply_discount tests
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [
    (-1, 10),
    (100, -5),
    (100, 105),
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize("qty,percent", [
    (10,5),(49,5),(50,10),(99,10),(100,15),(150,15),
])
def test_bulk_discount_percent(qty, percent):
    assert cart.bulk_discount_percent(qty) == percent

@pytest.mark.parametrize("qty", [0,-5,1.2,"a"])
def test_bulk_discount_percent_errors(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# parse_coupon tests
@pytest.mark.parametrize("code,result", [
    ("SAVE10",10),("save5",5),("  SAVE20 ",20),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", ["SAVEX", "SAVE0", "SAVE51", "", "X10", None, 123])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal,member,fee", [
    (0,False,60),(999.99,False,60),(1000,False,0),(1500,True,0),(500,True,30),
])
def test_shipping_fee(subtotal, member, fee):
    assert cart.shipping_fee(subtotal, member) == fee

@pytest.mark.parametrize("subtotal", [-1,-10])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart class tests
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_items(self):
        self.cart.add_item('apple', 100, quantity=2)
        self.cart.add_item('banana', 50)
        assert self.cart.items() == {'apple':2,'banana':1}

    def test_remove_item(self):
        self.cart.add_item('orange', 80, quantity=3)
        self.cart.remove_item('orange', quantity=1)
        assert self.cart.items()['orange'] == 2
        # Removing all
        self.cart.remove_item('orange', quantity=2)
        assert 'orange' not in self.cart.items()

    def test_subtotal(self):
        self.cart.add_item('a', 200, 3)   #600
        self.cart.add_item('b', 50, 4)    #200
        assert self.cart.subtotal() == 800.0

    def test_total_no_coupon_nonmember(self):
        self.cart.add_item('x', 500, 1)
        # subtotal 500, shipping 60 -> total 560
        assert cart.Cart().total(member=False) == 0.0  # empty cart
        assert_close(self.cart.total(member=False), 560.0)

    def test_total_with_coupon_and_member(self):
        self.cart.add_item('x', 400, 2)   #800 subtotal
        total = self.cart.total(member=True, coupon='SAVE10')
        # subtotal 800 -> discount 80 -> 720 + shipping member half of 60=30 =>750
        assert_close(total, 750.0)

    def test_total_empty_cart_no_shipping(self):
        c = cart.Cart()
        assert c.total() == 0.0

    def test_total_invalid_coupon_raises(self):
        self.cart.add_item('y', 100,1)
        with pytest.raises(ValueError):
            self.cart.total(coupon='BADCODE')
