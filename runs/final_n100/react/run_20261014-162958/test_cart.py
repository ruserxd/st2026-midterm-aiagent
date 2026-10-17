import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# Helper to compare floats with tolerance

def approx_equal(a,b,eps=1e-9):
    return abs(a-b) < eps

# Tests for apply_discount
@pytest.mark.parametrize("price,percent,expected",[
    (200,15,170.0),
    (100,0,100.0),
    (50,100,0.0),
])
def test_apply_discount_valid(price,percent,expected):
    assert approx_equal(apply_discount(price,percent), expected)

@pytest.mark.parametrize("price,percent",[
    (-1,10),
    (100,-5),
    (100,101),
])
def test_apply_discount_errors(price,percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# Tests for bulk_discount_percent
@pytest.mark.parametrize("qty,expected",[
    (9,0),
    (10,5),
    (49,5),
    (50,10),
    (99,10),
    (100,15),
    (150,15),
])
def test_bulk_discount(qty,expected):
    assert bulk_discount_percent(qty)==expected

@pytest.mark.parametrize("qty",[-1,0,3.5])
def test_bulk_discount_errors(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)

# Tests for parse_coupon
@pytest.mark.parametrize("code,expected",[
    ("SAVE10",10),
    ("save10 ",10),
    (" SAVE30",30),
])
def test_parse_coupon_valid(code,expected):
    assert parse_coupon(code)==expected

@pytest.mark.parametrize("code",["SAVEX", "SAVE0", "SAVE51", "abc10", ""])
def test_parse_coupon_errors(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# Tests for shipping_fee
@pytest.mark.parametrize("subtotal,member,expected",[
    (1000,False,0),
    (999.99,False,60),
    (500,True,30),
])
def test_shipping(subtotal,member,expected):
    assert shipping_fee(subtotal, member)==expected

@pytest.mark.parametrize("subtotal",[-10,-1])
def test_shipping_errors(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# Cart tests
class TestCart:
    def setup_method(self):
        self.cart = Cart()

    def test_add_and_items(self):
        self.cart.add_item("apple",10,2)
        self.cart.add_item("banana",5)
        items=self.cart.items()
        assert items["apple"]==(10,2)
        assert items["banana"]==(5,1)

    def test_remove(self):
        self.cart.add_item("apple",10,3)
        self.cart.remove_item("apple",2)
        assert self.cart.items()["apple"]==(10,1)
        # remove more than exists should delete item
        self.cart.remove_item("apple",5)
        assert "apple" not in self.cart.items()

    def test_subtotal(self):
        self.cart.add_item("apple",10,3)
        self.cart.add_item("banana",5,2)
        assert approx_equal(self.cart.subtotal(),10*3+5*2)

    def test_total_member_coupon(self):
        # setup: apple 3 at $10 each -> subtotal 30
        self.cart.add_item("apple",10,3)
        # coupon SAVE10 gives 10% off on subtotal before shipping
        total=self.cart.total(member=True,coupon="SAVE10")
        expected = (30*0.9)+30   # after discount + member shipping half of 60
        assert approx_equal(total,expected)
    
    def test_total_non_member_no_coupon(self):
        self.cart.add_item("item",20,5)  # subtotal=100
        total=self.cart.total()
        expected = 100+60  # no discount, full shipping
        assert approx_equal(total,expected)
