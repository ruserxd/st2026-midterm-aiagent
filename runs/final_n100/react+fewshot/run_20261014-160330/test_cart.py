import pytest
import cart

# apply_discount
@pytest.mark.parametrize("price, percent, expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# apply_discount errors
@pytest.mark.parametrize("price, percent", [(-1,10),(100,-5),(100,105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent
@pytest.mark.parametrize("quantity, expected", [
    (9,0),
    (10,5),
    (49,5),
    (50,10),
    (99,10),
    (100,15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# bulk_discount_percent errors
@pytest.mark.parametrize("quantity", [0,-1,3.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(int(quantity)) if isinstance(quantity,int) else cart.bulk_discount_percent(quantity)

# parse_coupon
@pytest.mark.parametrize("code, expected", [
    ("SAVE10",10),
    ("save25",25),
    ("   SaVe50  ",50),
])
def test_parse_coupon_valid(code,expected):
    assert cart.parse_coupon(code)==expected

# parse_coupon errors
@pytest.mark.parametrize("code", ["SAVE0","SAVE51","ABC10","SAVEXX","  "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee
@pytest.mark.parametrize("subtotal, member, expected", [
    (0,False,60),
    (500,True,30),
    (1000,False,0),
    (1500,True,0),
])
def test_shipping_fee(subtotal,member,expected):
    assert cart.shipping_fee(subtotal, member) == expected

# shipping_fee errors
@pytest.mark.parametrize("subtotal", [-10,-1.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart tests
class TestCart:
    def setup_method(self):
        self.cart=cart.Cart()

    def test_add_new_item(self):
        self.cart.add_item("apple",2.5,3)
        assert self.cart.items()=={"apple":3}

    def test_increment_item(self):
        self.cart.add_item("banana",1.0,2)
        self.cart.add_item("banana",1.0,4)
        assert self.cart.items()=={"banana":6}

    def test_price_mismatch(self):
        self.cart.add_item("orange",3.0,1)
        with pytest.raises(ValueError):
            self.cart.add_item("orange",4.0,2)

    def test_invalid_add_args(self):
        with pytest.raises(ValueError):
            self.cart.add_item("pear",-1.0,2)
        with pytest.raises(ValueError):
            self.cart.add_item("pear",1.0,0)

    def test_remove_partial(self):
        self.cart.add_item("mango",5.0,4)
        self.cart.remove_item("mango",2)
        assert self.cart.items()=={"mango":2}

    def test_remove_complete_and_remove_entry(self):
        self.cart.add_item("peach",2.0,3)
        self.cart.remove_item("peach",3)
        assert "peach" not in self.cart.items()

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("cherry",1)

    def test_subtotal_basic(self):
        self.cart.add_item("pen",1.2,5)  # subtotal 6.0
        assert self.cart.subtotal()==6.0
        # total includes shipping 60 => 66.0
        assert self.cart.total()==66.0

    def test_total_with_member_and_shipping(self):
        self.cart.add_item("book",200,3)  # subtotal 600
        assert self.cart.total(member=True)==630.0

    def test_total_bulk_discount(self):
        self.cart.add_item("widget",10,120)
        # subtotal 1200 -> bulk discount 15% -> 1020, shipping free
        assert self.cart.total()==1020.0

    def test_total_with_coupon(self):
        self.cart.add_item("gadget",50,1)
        expected_subtotal=50  # no bulk discount
        coupon_discount=cart.parse_coupon("SAVE20")
        total_after_coupon=round(expected_subtotal*(1-coupon_discount/100),2)
        shipping=cart.shipping_fee(50,member=False)
        assert self.cart.total(coupon="SAVE20")==total_after_coupon+shipping
