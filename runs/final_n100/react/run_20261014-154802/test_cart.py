import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# Test apply_discount linear discount.
def test_apply_discount():
    assert apply_discount(100.0, 10) == 90.0
    assert round(apply_discount(50.5, 25), 2) == 37.88
    assert apply_discount(20.0, 0) == 20.0

# Test bulk discount tiers.
def test_bulk_discount_percent():
    # Assuming thresholds: <5:0%, 5-9:10%, >=10:20%
    for qty, expected in [(1,0),(4,0),(5,10),(9,10),(10,20),(15,20)]:
        assert bulk_discount_percent(qty) == expected

# parse_coupon returns int percent or raises.
def test_parse_coupon_valid():
    code = "SAVE10"
    pct = parse_coupon(code)
    assert isinstance(pct,int)
    assert 0 <= pct <= 100

def test_parse_coupon_invalid():
    with pytest.raises(ValueError):
        parse_coupon("")

# shipping_fee: base 5 + 0.1 per unit.
def test_shipping_fee():
    assert shipping_fee(subtotal=0, member=False) == 0
    assert round(shipping_fee(subtotal=100, member=True),2) == 5+0.1*1
    assert round(shipping_fee(subtotal=200, member=False),2) == 5+0.1*5

# Cart tests.
class TestCart:
    def setup_method(self):
        self.cart = Cart()

    def test_add_and_items(self):
        self.cart.add_item("apple", 0.5, quantity=3)
        assert self.cart.items()["apple"] == (0.5,3)

    def test_remove_item(self):
        self.cart.add_item("cherry",0.3,quantity=10)
        self.cart.remove_item("cherry",4)
        assert self.cart.items()["cherry"]==(0.3,6)
        self.cart.remove_item("cherry",6)
        assert "cherry" not in self.cart.items()

    def test_subtotal(self):
        self.cart.add_item("item1",2.0,quantity=3)
        self.cart.add_item("item2",5.5)
        assert self.cart.subtotal()==11.5

    def test_total_no_coupon(self):
        self.cart.add_item("widget",10,quantity=2)
        expected = 20 + 5 + 0.2
        assert round(self.cart.total(),2)==expected

    def test_empty_cart(self):
        assert self.cart.total()==0
