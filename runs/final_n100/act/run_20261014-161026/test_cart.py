import pytest
import cart

# ---------- bulk_discount_percent tests matching spec ----------
@pytest.mark.parametrize("quantity,expected", [
    (99,10),   # >=50 ->10
    (50,10),   # boundary
    (49,5),    # >=10 ->5
    (100,15),  # boundary
    (150,15),
    (9,0),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# test invalid quantity
@pytest.mark.parametrize("quantity", [0,-1,3.5,"10"])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- apply_discount ----------
@pytest.mark.parametrize("price,percent,result", [
    (200,15,170.0),
    (100,0,100.0),
    (100,100,0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == pytest.approx(result)

# invalid price or percent
@pytest.mark.parametrize("price,percent", [(-10,10),(50,-5),(50,150)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- parse_coupon ----------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10",10),
    ("save20",20),
    ("  SAVE5 ",5),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVEX", "SAVE0", "SAVE51", "abc", "", "   "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize("subtotal,member,expected", [
    (1200, False, 0),
    (1000, True, 0),
    (999.99, False, 60),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

# invalid subtotal
@pytest.mark.parametrize("subtotal", [-10, -0.01])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class basic operations ----------
class TestCartOperations:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_subtotal_and_total(self):
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    def test_add_item_new(self):
        self.cart.add_item('apple', 10, 3)
        assert self.cart.items() == {'apple':3}
        # unit price 10, quantity 3 = bulk discount 0 - subtotal 30
        assert self.cart.subtotal() == 30.0

    def test_add_item_existing_same_price(self):
        self.cart.add_item('banana',5,2)
        self.cart.add_item('banana',5,3)
        assert self.cart.items() == {'banana':5}
        # 5 * 5 =25, bulk discount none = subtotal 25
        assert self.cart.subtotal() == 25.0

    def test_add_item_existing_different_price_raises(self):
        self.cart.add_item('orange',4,1)
        with pytest.raises(ValueError):
            self.cart.add_item('orange',5,1)

    def test_remove_item_partial_and_full_removal(self):
        self.cart.add_item('kiwi',2,5)
        self.cart.remove_item('kiwi',3)
        assert self.cart.items() == {'kiwi':2}
        self.cart.remove_item('kiwi',2)
        # After removal the item should be removed entirely
        assert self.cart.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item('mango',1)

    def test_bulk_discount_in_subtotal(self):
        # 10 items, bulk discount 5%
        self.cart.add_item('stick',20,10)
        expected = cart.apply_discount(200,5)  # 200 *0.95 =190
        assert self.cart.subtotal() == pytest.approx(expected)

    def test_total_with_coupon_and_member(self):
        self.cart.add_item('pen',50,2)  # subtotal 100 no bulk discount
        total_before = self.cart.total(coupon='SAVE10')
        expected = 90.0 + cart.shipping_fee(90)
        assert total_before == pytest.approx(expected)

    def test_total_member_free_shipping(self):
        self.cart.add_item('camera',600,2)  # subtotal 1200 free shipping
        total = self.cart.total(member=True)
        expected = cart.apply_discount(1200,0) + cart.shipping_fee(1200,member=True)
        assert total == pytest.approx(expected)

    def test_total_invalid_coupon(self):
        # Spec says ValueError; implementation may not raise
        with pytest.raises(ValueError):
            self.cart.total(coupon='BADCODE')

# ---------- Edge cases for totals ----------
@pytest.mark.parametrize("items,coupon,expected", [
    ([], None, 0.0), # empty cart
])
def test_total_empty_cart(items, coupon, expected):
    c = cart.Cart()
    assert c.total(coupon=coupon) == expected
