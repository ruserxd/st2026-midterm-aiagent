import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

@pytest.fixture
def empty_cart():
    return Cart()

class TestApplyDiscount:
    def test_basic(self):
        assert apply_discount(200, 15) == 170.0
    def test_rounding(self):
        assert apply_discount(99, 1) == 98.01
    def test_zero_percent(self):
        assert apply_discount(100, 0) == 100.0
    def test_full_percent(self):
        assert apply_discount(50, 100) == 0.0
    @pytest.mark.parametrize("price, percent", [(-1, 10), (10, -5), (10, 105)])
    def test_invalid_inputs(self, price, percent):
        with pytest.raises(ValueError):
            apply_discount(price, percent)

class TestBulkDiscountPercent:
    @pytest.mark.parametrize("qty, expected", [(9,0),(10,5),(49,5),(50,10),(99,10),(100,15),(150,15)])
    def test_discounts(self, qty, expected):
        assert bulk_discount_percent(qty)==expected
    @pytest.mark.parametrize("qty", [0,-5])
    def test_invalid_qty(self, qty):
        with pytest.raises(ValueError):
            bulk_discount_percent(qty)

class TestParseCoupon:
    @pytest.mark.parametrize("code, expected", [("SAVE10",10),("save20",20),("  Save5 ",5)])
    def test_valid(self, code, expected):
        assert parse_coupon(code)==expected
    @pytest.mark.parametrize("code", ["save0","save51","SAVE-5","DISCOUNT10","",123])
    def test_invalid(self, code):
        with pytest.raises(ValueError):
            parse_coupon(code)

class TestShippingFee:
    def test_free_shipping(self):
        assert shipping_fee(1000)==0 and shipping_fee(2000)==0
    def test_non_member(self):
        assert shipping_fee(999)==60
    def test_member(self):
        assert shipping_fee(999, member=True)==30
    @pytest.mark.parametrize("subtotal", [-1,-100])
    def test_invalid_subtotal(self, subtotal):
        with pytest.raises(ValueError):
            shipping_fee(subtotal)

class TestCart:
    def test_initial_empty(self, empty_cart: Cart):
        assert empty_cart.items()=={}
        assert empty_cart.subtotal()==0.0
        # subtotal 0 => shipping fee 60 for non-member
        assert empty_cart.total()==60.0
    def test_add_and_remove_items(self, empty_cart: Cart):
        c=empty_cart
        c.add_item("apple",100,quantity=2)
        assert c.items()["apple"]==(100,2)
        assert c.subtotal()==200.0
        c.add_item("apple",100,quantity=3)
        assert c.items()["apple"]==(100,5)
        c.remove_item("apple",quantity=2)
        assert c.items()["apple"]==(100,3)
        c.remove_item("apple",quantity=5)
        assert "apple" not in c.items()
    def test_total_with_discounts_and_coupons(self, empty_cart: Cart):
        c=empty_cart
        c.add_item("widget",200,quantity=12)  # bulk discount 5%
        subtotal=200*12
        discounted=subtotal-apply_discount(subtotal,0)+apply_discount(subtotal,bulk_discount_percent(12))
        # easier: compute expected using functions
        expected = apply_discount(subtotal, bulk_discount_percent(12))
        expected = apply_discount(expected, parse_coupon("SAVE10"))
        assert c.total(coupon="SAVE10")==pytest.approx(expected)
    def test_member_shipping(self, empty_cart: Cart):
        c=empty_cart
        c.add_item("item",200,quantity=2)
        # subtotal 400 <1000, member half fee
        assert c.total(member=True)==pytest.approx(400+30)
    def test_total_no_items(self, empty_cart: Cart):
        assert empty_cart.total()==60.0
