import pytest
import cart

# ---------- apply_discount -------------------------------------------------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),   # example
    (100, 0, 100.0),    # no discount
    (50, 100, 0.0),     # full free
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# price negative raises ValueError
@pytest.mark.parametrize("price", [-1, -10.5])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 20)

# percent out of bounds raises ValueError
for bad in [-5, 101]:
    def _bad_percent(bad=bad):
        with pytest.raises(ValueError):
            cart.apply_discount(100, bad)
    globals()[f"test_apply_discount_bad_percent_{bad}"] = _bad_percent

# ---------- bulk_discount_percent ----------------------------------------
@pytest.mark.parametrize("quantity,percent", [
    (1, 0), (9, 0), (10,5), (49,5), (50,10), (99,10), (100,15), (150,15)
])
def test_bulk_discount_percent(quantity, percent):
    assert cart.bulk_discount_percent(quantity) == percent

# quantity non-positive or not int raises ValueError
for bad in [0,-1,5.5,"ten"]:
    def _bad_qty(bad=bad):
        with pytest.raises(ValueError):
            cart.bulk_discount_percent(bad)
    globals()[f"test_bulk_discount_percent_bad_{repr(bad)}"] = _bad_qty

# ---------- parse_coupon -----------------------------------------------
@pytest.mark.parametrize("code,percent", [
    ("SAVE10",10), ("save20",20), (" SAVE30 ",30),
])
def test_parse_coupon_valid(code, percent):
    assert cart.parse_coupon(code) == percent

# invalid codes raise ValueError
for bad in ["SAV10", "SAVE0", "SAVE51", "", "  "]:
    def _bad_code(bad=bad):
        with pytest.raises(ValueError):
            cart.parse_coupon(bad)
    globals()[f"test_parse_coupon_invalid_{repr(bad)}"] = _bad_code

# ---------- shipping_fee -----------------------------------------------
@pytest.mark.parametrize("subtotal,fee", [
    (0,60), (999.99,60), (1000,0), (1500,0)
])
def test_shipping_fee(subtotal, fee):
    assert cart.shipping_fee(subtotal) == fee
    # member pays half
    if subtotal < 1000:
        assert cart.shipping_fee(subtotal, member=True) == fee/2
    else:
        assert cart.shipping_fee(subtotal, member=True) == 0

# negative subtotal raises ValueError
for bad in [-1,-10.5]:
    def _bad_sub(bad=bad):
        with pytest.raises(ValueError):
            cart.shipping_fee(bad)
    globals()[f"test_shipping_fee_negative_{bad}"] = _bad_sub

# ---------- Cart class -----------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initially_empty(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    def test_add_item_new_and_existing(self):
        self.cart.add_item("apple", 100, 3)
        assert self.cart.items() == {"apple":3}
        # add same again with same price
        self.cart.add_item("apple", 100, 2)
        assert self.cart.items() == {"apple":5}

    def test_add_item_price_mismatch_raises(self):
        self.cart.add_item("banana", 200,1)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 250,1)

    def test_remove_item_partial_and_full(self):
        self.cart.add_item("pear", 150,5)
        self.cart.remove_item("pear",2)
        assert self.cart.items() == {"pear":3}
        self.cart.remove_item("pear",3)
        assert self.cart.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("orange",1)

    def test_subtotal_with_bulk_discount(self):
        # 10 units -> 5% discount, unit price 200
        self.cart.add_item("widget", 200,10)
        expected = cart.apply_discount(200*10, 5)  # 2000-100=1900
        assert self.cart.subtotal() == round(expected,2)

    def test_total_without_coupon(self):
        self.cart.add_item("gadget", 300,2)  # no bulk discount
        subtotal = 600.0
        shipping = cart.shipping_fee(subtotal)
        assert self.cart.total() == round(subtotal + shipping,2)

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("tool", 1000,1)
        # subtotal 1000 -> no bulk discount
        subtotal = 1000.0
        coupon_percent = cart.parse_coupon("SAVE20")
        after_coupon = cart.apply_discount(subtotal, coupon_percent)
        shipping = cart.shipping_fee(after_coupon, member=True)  # free if >=1000
        expected_total = round(after_coupon + shipping,2)
        assert self.cart.total(member=True, coupon="SAVE20") == expected_total

    def test_empty_cart_no_shipping(self):
        assert self.cart.total() == 0.0
