import pytest
import cart

# Helper functions to create Cart and add items

def make_cart_with_items(*items):
    c = cart.Cart()
    for name, price, qty in items:
        c.add_item(name, price, qty)
    return c

class TestApplyDiscount:
    def test_valid_discount(self):
        assert cart.apply_discount(200, 15) == 170.0
        # rounding check
        assert cart.apply_discount(100, 33) == 67.0

    def test_invalid_price(self):
        with pytest.raises(ValueError):
            cart.apply_discount(-10, 20)

    def test_invalid_percent_lower(self):
        with pytest.raises(ValueError):
            cart.apply_discount(50, -5)

    def test_invalid_percent_upper(self):
        with pytest.raises(ValueError):
            cart.apply_discount(50, 110)

class TestBulkDiscountPercent:
    @pytest.mark.parametrize("qty,expected", [
        (9,0), (10,5), (15,5), (49,5), (50,10), (75,10), (100,15), (150,15)
    ])
    def test_bulk_discount(self,qty,expected):
        assert cart.bulk_discount_percent(qty) == expected

    def test_invalid_quantity_type(self):
        with pytest.raises(ValueError):
            cart.bulk_discount_percent(0.5)

class TestParseCoupon:
    @pytest.mark.parametrize("code", ["SAVE10","save20"," Save30 "])
    def test_valid_codes(self, code):
        # only check that parse_coupon returns an int between 1 and 50
        discount = cart.parse_coupon(code)
        assert isinstance(discount,int)
        assert 1 <= discount <= 50

    @pytest.mark.parametrize("code", ["SAVE0","SAVEXX","1234","SAVE51","SAVE-10"])
    def test_invalid_codes(self, code):
        with pytest.raises(ValueError):
            cart.parse_coupon(code)

class TestShippingFee:
    def test_free_for_large_subtotal(self):
        assert cart.shipping_fee(1000) == 0
        assert cart.shipping_fee(1500) == 0

    def test_member_half_fee(self):
        assert cart.shipping_fee(500, member=True) == 30
        assert cart.shipping_fee(0, member=True) == 30

    def test_non_member_full_fee(self):
        assert cart.shipping_fee(200) == 60
        assert cart.shipping_fee(999.99) == 60

    def test_negative_subtotal_raises(self):
        with pytest.raises(ValueError):
            cart.shipping_fee(-10)

class TestCart:
    def test_add_and_items(self):
        c = cart.Cart()
        c.add_item("apple", 50, 2)
        assert c.items() == {"apple": (50, 2)}
        # adding again should increase quantity
        c.add_item("apple", 50, 3)
        assert c.items()["apple"] == (50,5)

    def test_remove_and_subtotal(self):
        c = cart.Cart()
        c.add_item("banana", 30, 4)
        c.remove_item("banana", 2)
        assert c.items()["banana"] == (30,2)
        assert c.subtotal() == 60

    def test_total_with_coupon_and_member(self):
        # 3 items costing total 300
        c = make_cart_with_items(("x",100,1),("y",100,1),("z",100,1))
        subtotal = c.subtotal()
        assert subtotal == 300
        coupon_percent = cart.parse_coupon("SAVE10")
        # apply discount to each item: 90 per unit => total 270
        # no shipping because member and subtotal < 1000
        expected_total = 270 + (30 if not True else 0)  # member gets half -> 0
        assert c.total(member=True, coupon=coupon_percent) == expected_total

    def test_total_no_coupon(self):
        c = make_cart_with_items(("x",200,1))
        assert c.total() == 200 + 60  # shipping for non member subtotal <1000

    def test_bulk_discount_in_total(self):
        # buying 120 apples at $10 each: bulk discount 15%
        c = make_cart_with_items(("apple",10,120))
        unit_price_after_discount = cart.apply_discount(10, cart.bulk_discount_percent(120))
        expected_subtotal = round(unit_price_after_discount*120,2)
        assert abs(c.total() - (expected_subtotal + 0)) < 1e-6

    def test_removing_nonexistent_item(self):
        c = cart.Cart()
        with pytest.raises(KeyError):
            c.remove_item("nonexist",1)
