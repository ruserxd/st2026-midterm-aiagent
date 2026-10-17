import pytest
import cart

# Helper to round as the module does
round2 = lambda x: round(x, 2)

# ---------- apply_discount -----------
@pytest.mark.parametrize("price, percent, expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (123.45, 20, round(98.76,2)),
])
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price, percent", [(-10, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent -----------
@pytest.mark.parametrize("quantity, expected", [
    (9, 0), (10,5), (49,5), (50,10), (99,10), (100,15), (150,15)
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 3.5, "a"])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon -----------
@pytest.mark.parametrize("code, expected", [
    ("SAVE10",10), ("save20",20), ("  SaVe5 ",5), ("SAVE1",1), ("SAVE50",50)
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAV10", "SAVE0", "SAVE51", "SAVE-5", "  ", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee -----------
@pytest.mark.parametrize("subtotal, member, expected", [
    (0, False, 60), (999.99, False, 60), (1000, False, 0),
    (200, True, 30), (1500, True, 0)
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart functionality -----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_subtotal_and_total(self):
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    def test_add_item_new(self):
        self.cart.add_item("apple", 2.5, 3)
        assert self.cart.items() == {"apple": 3}
        # subtotal: 3 * 2.5 = 7.5 -> no bulk discount (qty<10)
        assert self.cart.subtotal() == 7.5

    def test_add_item_existing_same_price(self):
        self.cart.add_item("banana", 1.0, 5)
        self.cart.add_item("banana", 1.0, 4)
        assert self.cart.items() == {"banana":9}
        assert self.cart.subtotal() == 9.0

    def test_add_item_existing_different_price_raises(self):
        self.cart.add_item("orange", 3.0, 2)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 4.0, 1)

    def test_remove_item_partial_and_complete(self):
        self.cart.add_item("mango", 5.0, 10)  # triggers bulk discount 5%
        assert self.cart.items() == {"mango":10}
        # subtotal before removal: 10*5=50 -> 5% discount = 47.5
        assert self.cart.subtotal() == 47.5
        self.cart.remove_item("mango", 3)
        assert self.cart.items() == {"mango":7}
        # new subtotal: 7*5=35, qty<10 => no bulk discount
        assert self.cart.subtotal() == 35.0
        self.cart.remove_item("mango", 7)
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("pear", 1)

    def test_total_with_coupon_and_shipping(self):
        # Add two items, one triggers bulk discount
        self.cart.add_item("itemA", 100.0, 10)  # qty=10 -> 5% off
        self.cart.add_item("itemB", 200.0, 3)
        # Subtotal before coupon: itemA=100*10=1000-5%=950; itemB=600 -> 1550
        assert round2(self.cart.subtotal()) == 1550.0
        # Apply coupon SAVE20 (20% off subtotal)
        total = self.cart.total(coupon="SAVE20")
        # After coupon: 1550*0.8 = 1240; shipping fee non-member on 1240 >1000 -> free
        assert round2(total) == 1240.0
        # Now member gets half shipping but still free
        total_member = self.cart.total(coupon="SAVE20", member=True)
        assert round2(total_member) == 1240.0

    def test_total_no_coupon_and_nonmember(self):
        self.cart.add_item("gadget", 500.0, 1)
        # subtotal=500; after coupon none ->500; shipping fee: 60 (non-member)
        assert round2(self.cart.total()) == 560.0

    def test_total_invalid_coupon_raises(self):
        self.cart.add_item("foo", 10.0, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")
