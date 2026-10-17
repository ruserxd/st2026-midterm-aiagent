import pytest
import cart

# ---------- apply_discount ----------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),           # example
    (100, 0, 100.0),            # no discount
    (50, 100, 0.0),             # full discount
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# negative price or invalid percent
@pytest.mark.parametrize("price,percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize("qty,percent", [
    (9,0), (10,5), (49,5), (50,10), (99,10), (100,15), (150,15)
])
def test_bulk_discount(qty, percent):
    assert cart.bulk_discount_percent(qty) == percent

@pytest.mark.parametrize("qty", [0,-1,3.5])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- parse_coupon ----------
valid_codes = {
    "SAVE10":10,
    "save20":20,
    "  Save30 ":30,
}
@pytest.mark.parametrize("code,percent", list(valid_codes.items()))
def test_parse_coupon_valid(code, percent):
    assert cart.parse_coupon(code) == percent

invalid_codes = ["SAVEX", "save0", "save51", "foo10", "  ", "SAVE"]
@pytest.mark.parametrize("code", invalid_codes)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize("subtotal,member,fee", [
    (0, False, 60),
    (999.99, False, 60),
    (1000, False, 0),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, fee):
    assert cart.shipping_fee(subtotal, member) == fee

# negative subtotal
@pytest.mark.parametrize("subtotal", [-1,-10.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_item_new_and_existing(self):
        self.cart.add_item("apple", 2.0, quantity=3)
        assert self.cart.items() == {"apple":3}
        # add more of same item
        self.cart.add_item("apple", 2.0, quantity=2)
        assert self.cart.items() == {"apple":5}

    def test_add_item_price_mismatch(self):
        self.cart.add_item("banana", 1.5)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 2.0)

    def test_add_item_invalid(self):
        with pytest.raises(ValueError):
            self.cart.add_item("pear", -1.0)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 1.0, quantity=0)

    def test_remove_item(self):
        self.cart.add_item("orange", 3.0, quantity=4)
        self.cart.remove_item("orange", quantity=2)
        assert self.cart.items() == {"orange":2}
        # remove remaining
        self.cart.remove_item("orange", quantity=2)
        assert self.cart.items() == {}

    def test_remove_item_not_exist(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent")

    def test_subtotal_bulk_discount(self):
        # 12 apples at $10 each => bulk discount 5%
        self.cart.add_item("apple", 10.0, quantity=12)
        expected = round(10.0*12*(1-0.05),2)  # 10*12=120, 5% off ->108
        assert self.cart.subtotal() == expected

    def test_total_no_coupon_member(self):
        self.cart.add_item("item", 20.0, quantity=1)
        subtotal = self.cart.subtotal()
        # member => shipping half of 60 =30
        expected = round(subtotal + 30,2)
        assert self.cart.total(member=True) == expected

    def test_total_coupon(self):
        self.cart.add_item("item", 200.0, quantity=1)
        subtotal = self.cart.subtotal()
        # coupon SAVE10 -> 10% off subtotal
        amount_after_coupon = cart.apply_discount(subtotal,10)
        expected = round(amount_after_coupon + 60,2)  # not member so shipping 60
        assert self.cart.total(coupon="SAVE10") == expected

    def test_total_invalid_coupon(self):
        self.cart.add_item("item", 50.0)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

    def test_total_empty_cart(self):
        assert self.cart.total() == 0
