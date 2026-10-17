import pytest
import cart

# ---------- apply_discount ---------------------------------------------------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),            # example from spec
    (100, 0, 100.0),             # no discount
    (50, 100, 0.0),              # full discount
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# invalid price / percent
@pytest.mark.parametrize("price,percent", [(-1, 10), (50, -5), (50, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ------------------------------------------
@pytest.mark.parametrize("qty,percent", [
    (9, 0),   # less than 10
    (10, 5),  # exactly 10
    (49, 5),  # just below 50
    (50, 10), # exactly 50
    (99, 10), # just below 100
    (100, 15),# exactly 100
])
def test_bulk_discount_percent(qty, percent):
    assert cart.bulk_discount_percent(qty) == percent

@pytest.mark.parametrize("qty", [0, -5, 1.2])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- parse_coupon ----------------------------------------------------
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    ("save25", 25),
    (" SAVE5 ", 5),
])
def test_parse_coupon(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", ["INVALID", "SAVE0", "SAVE51", "1234", "SAVEX"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee -----------------------------------------------------
@pytest.mark.parametrize("subtotal,member,fee", [
    (0, False, 60),
    (999.99, True, 30),
    (1000, False, 0),
])
def test_shipping_fee(subtotal, member, fee):
    assert cart.shipping_fee(subtotal, member) == fee

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class -------------------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initial_state(self):
        assert list(self.cart.items().keys()) == []
        assert self.cart.subtotal() == 0
        assert self.cart.total() == 0

    def test_add_item_new(self):
        self.cart.add_item("apple", 1.5, quantity=2)
        assert self.cart.items() == {"apple": 2}
        # subtotal: 1.5*2 = 3.0 (no bulk discount)
        assert self.cart.subtotal() == 3.0

    def test_add_item_increase(self):
        self.cart.add_item("banana", 0.75, quantity=10)   # triggers 5% discount
        # unit price 0.75*10 = 7.5, bulk 5% -> 6.75
        assert self.cart.subtotal() == 6.75
        self.cart.add_item("banana", 0.75, quantity=90)   # now total qty 100 triggers 15%
        # subtotal for bananas: 0.75*100 = 75.0, bulk 15% -> 63.75
        assert self.cart.subtotal() == 63.75

    def test_add_item_price_mismatch(self):
        self.cart.add_item("orange", 1.0)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 2.0, quantity=1)

    def test_remove_item(self):
        self.cart.add_item("kiwi", 0.5, quantity=3)
        self.cart.remove_item("kiwi", quantity=2)
        assert self.cart.items() == {"kiwi": 1}
        self.cart.remove_item("kiwi", quantity=1)  # should remove entirely
        assert self.cart.items() == {}

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexist")

    def test_subtotal_with_bulk_discounts(self):
        # 10 apples -> 5% discount
        self.cart.add_item("apple", 2.0, quantity=10)
        assert self.cart.subtotal() == round(2.0*10 * 0.95, 2)  # 19.0
        # add 50 oranges -> 10% discount on that item only
        self.cart.add_item("orange", 1.0, quantity=50)
        subtotal_expected = round(2.0*10*0.95 + 1.0*50*0.9, 2)
        assert self.cart.subtotal() == subtotal_expected

    def test_total_with_coupon_and_shipping(self):
        # items total to 200 after bulk discount
        self.cart.add_item("item", 10.0, quantity=20)   # 5% off -> 190
        coupon_percent = cart.parse_coupon("SAVE10")     # 10%
        subtotal_after_coupon = round(190 * 0.9, 2)
        shipping = cart.shipping_fee(subtotal_after_coupon)
        total_expected = round(subtotal_after_coupon + shipping, 2)
        assert self.cart.total(coupon="SAVE10") == total_expected

    def test_total_with_member_and_no_shipping(self):
        # subtotal >=1000, free shipping
        self.cart.add_item("expensive", 500.0, quantity=3)   # no bulk discount -> 1500
        assert self.cart.total(member=True) == 1500.00

    def test_total_empty_cart_no_shipping(self):
        assert self.cart.total() == 0

    def test_total_invalid_coupon(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

    def test_total_member_flag_ignored_when_no_items(self):
        assert cart.Cart().total(member=True) == 0
