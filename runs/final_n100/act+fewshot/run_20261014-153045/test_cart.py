import pytest
import cart

EPS = 1e-9

def assert_close(a,b):
    assert abs(a-b) < EPS

###################### apply_discount tests ##########################
@pytest.mark.parametrize("price,percent,result", [
    (200,15,170.0),
    (100,0,100.0),
    (100,100,0.0)
])
def test_apply_discount_valid(price,percent,result):
    assert cart.apply_discount(price,percent)==result

@pytest.mark.parametrize("price,percent", [(-1,10),(100,-5),(100,101)])
def test_apply_discount_invalid(price,percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price,percent)

###################### bulk_discount_percent tests ##################
@pytest.mark.parametrize("qty,expected", [
    (9,0),(10,5),(49,5),(50,10),(99,10),(100,15),(150,15)
])
def test_bulk_discount_percent(qty,expected):
    assert cart.bulk_discount_percent(qty)==expected

@pytest.mark.parametrize("qty", [0,-1,3.2])
def test_bulk_discount_percent_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

###################### parse_coupon tests ##########################
@pytest.mark.parametrize("code,percent", [
    ("SAVE10",10),("save20 ",20),("  SAVE5",5),("save50",50)
])
def test_parse_coupon_valid(code,percent):
    assert cart.parse_coupon(code)==percent

@pytest.mark.parametrize("code", ["SAVE0","SAVE51","FOO10","SAVE-5","save","", "   "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

###################### shipping_fee tests ##########################
@pytest.mark.parametrize("subtotal,member,result", [
    (0,False,60),(500,True,30),(1000,False,0),(2000,True,0)
])
def test_shipping_fee(subtotal,member,result):
    assert cart.shipping_fee(subtotal,member)==result

@pytest.mark.parametrize("subtotal", [-1,-100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

###################### Cart tests ##########################
class TestCart:
    def setup_method(self):
        self.c=cart.Cart()

    def test_add_and_items(self):
        self.c.add_item("apple",1.00,3)
        self.c.add_item("banana",0.50,2)
        assert self.c.items()=={"apple":3,"banana":2}

    def test_add_existing_increase_quantity(self):
        self.c.add_item("apple",1.00,2)
        self.c.add_item("apple",1.00,1)
        assert self.c.items() == {"apple":3}

    def test_add_existing_wrong_price(self):
        self.c.add_item("apple",1.00,1)
        with pytest.raises(ValueError):
            self.c.add_item("apple",2.00,1)

    def test_remove_item_partial(self):
        self.c.add_item("apple",1.00,3)
        self.c.remove_item("apple",2)
        assert self.c.items()=={"apple":1}

    def test_remove_item_complete_removal(self):
        self.c.add_item("apple",1.00,2)
        self.c.remove_item("apple",2)
        assert self.c.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.c.remove_item("pear",1)

    def test_subtotal_no_bulk_discount(self):
        self.c.add_item("apple",2.00,5)  # qty<10 no discount
        assert abs(self.c.subtotal() - 10.0) < EPS

    def test_subtotal_with_bulk_discount(self):
        self.c.add_item("banana",1.00,50)
        expected = round(1.00*50*(1-0.10),2)
        assert abs(self.c.subtotal() - expected) < EPS

    def test_total_no_coupon_member_false(self):
        self.c.add_item("item",100.0,5)  # no bulk discount
        total = self.c.total(member=False)
        assert_close(total,560.0)

    def test_total_with_coupon_and_member(self):
        self.c.add_item("item",200.0,1)
        assert_close(self.c.total(member=True,coupon="SAVE10"),210.0)

    def test_total_empty_cart(self):
        assert self.c.total() == 0.0
