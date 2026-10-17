import pytest
import cart

# --- Utility helpers -----------------------------------------------------

def round2(x):
    return round(float(x), 2)

# --- apply_discount -------------------------------------------------------

def test_apply_discount_normal():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0

# Boundary percent values
@pytest.mark.parametrize("price,percent",[(0,0),(10,0),(20,100)])
def test_apply_discount_boundary_percent(price, percent):
    # percent 0 or 100 should work
    if percent==0:
        expected = price
    else:  # 100
        expected = 0.0
    assert cart.apply_discount(price, percent) == expected

# Negative price or percent out of range raise ValueError
@pytest.mark.parametrize("price",[-1, -5])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent",[-10,-1,101,150])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# --- bulk_discount_percent -------------------------------------------------
@staticmethod
class TestBulk:
    def test_bulk_0(self):
        assert cart.bulk_discount_percent(9) == 0
    def test_bulk_5(self):
        assert cart.bulk_discount_percent(10) == 5
    def test_bulk_10(self):
        assert cart.bulk_discount_percent(50) == 10
    def test_bulk_15(self):
        assert cart.bulk_discount_percent(100) == 15

@staticmethod
class TestBulkErrors:
    @pytest.mark.parametrize("qty",[0,-5,1.5])
    def test_negative_or_nonint(self, qty):
        with pytest.raises(ValueError):
            cart.bulk_discount_percent(qty)

# --- parse_coupon ---------------------------------------------------------
@staticmethod
class TestParseCoupon:
    @pytest.mark.parametrize("code",["SAVE10","save10","  SAVE20  "])
    def test_valid(self, code):
        # expected percent is the integer after SAVE
        prefix="SAVE"
        cleaned=code.strip().upper()
        assert cleaned.startswith(prefix)
        n=int(cleaned[len(prefix):])
        assert cart.parse_coupon(code) == n

    @pytest.mark.parametrize("code",["sAVe0","save51","discount10","1234","SAVE-5"])
    def test_invalid(self, code):
        with pytest.raises(ValueError):
            cart.parse_coupon(code)

# --- shipping_fee ---------------------------------------------------------
@staticmethod
class TestShipping:
    def test_free_above_1000(self):
        assert cart.shipping_fee(1000) == 0
        assert cart.shipping_fee(1200) == 0

    def test_normal_non_member(self):
        assert cart.shipping_fee(999) == 60

    def test_member_half(self):
        assert cart.shipping_fee(500, member=True) == 30

    @pytest.mark.parametrize("subtotal",[-1,-5])
    def test_negative_subtotal(self, subtotal):
        with pytest.raises(ValueError):
            cart.shipping_fee(subtotal)

# --- Cart class -----------------------------------------------------------
class TestCartBasic:
    def setup_method(self):
        self.c = cart.Cart()

    def test_initial_empty(self):
        assert self.c.items() == {}
        assert self.c.subtotal() == 0.0
        assert self.c.total() == 0.0

    def test_add_item_new(self):
        self.c.add_item("apple", unit_price=2, quantity=3)
        assert self.c.items() == {"apple":3}
        # subtotal: 2*3 =6 no bulk discount
        assert self.c.subtotal() == 6.0

    def test_add_multiple_same(self):
        self.c.add_item("banana", unit_price=1, quantity=5)
        self.c.add_item("banana", unit_price=1, quantity=6)
        # total quantity 11 -> bulk discount 5%
        assert self.c.items() == {"banana":11}
        subtotal = 1*11
        expected = cart.apply_discount(subtotal, 5)
        assert self.c.subtotal() == round2(expected)

    def test_add_invalid_price(self):
        with pytest.raises(ValueError):
            self.c.add_item("x", unit_price=-1, quantity=1)

    def test_add_invalid_qty(self):
        with pytest.raises(ValueError):
            self.c.add_item("y", unit_price=5, quantity=0)

    def test_add_conflicting_price(self):
        self.c.add_item("z", unit_price=3, quantity=2)
        with pytest.raises(ValueError):
            self.c.add_item("z", unit_price=4, quantity=1)

    def test_remove_item_partial(self):
        self.c.add_item("t", 10, quantity=5)
        self.c.remove_item("t", quantity=3)
        assert self.c.items() == {"t":2}

    def test_remove_all_removes_entry(self):
        self.c.add_item("u", 4, quantity=2)
        self.c.remove_item("u", quantity=2)
        assert self.c.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.c.remove_item("doesnotexist", quantity=1)

    def test_total_no_coupon_member(self):
        # add items totaling 500, no coupon, member True -> shipping 30
        self.c.add_item("item", unit_price=50, quantity=10)  # 500 no bulk discount
        total = 500 + cart.shipping_fee(500, member=True)
        assert self.c.total(member=True) == round2(total)

    def test_total_with_coupon(self):
        self.c.add_item("item", unit_price=20, quantity=5)  # 100 no bulk discount
        total_before = 100 + cart.shipping_fee(100)
        coupon_percent = cart.parse_coupon("SAVE10")
        after_coupon = cart.apply_discount(total_before, coupon_percent)
        expected = after_coupon + cart.shipping_fee(after_coupon)
        assert self.c.total(coupon="SAVE10") == round2(expected)

    def test_total_invalid_coupon(self):
        with pytest.raises(ValueError):
            self.c.total(coupon="BADCODE")

    def test_total_empty_no_shipping(self):
        assert self.c.total() == 0.0

# Edge cases for rounding
class TestCartRounding:
    def setup_method(self):
        self.c = cart.Cart()

    def test_subtotal_rounding(self):
        # quantity that gives a non-integer subtotal after discount
        self.c.add_item("x", unit_price=0.1, quantity=101)  # bulk 5%
        raw = 0.1*101
        discounted = cart.apply_discount(raw, 5)
        assert round2(discounted) == round2(cart.subtotal())

    def test_total_rounding(self):
        self.c.add_item("y", unit_price=0.33, quantity=10)  # bulk 5%
        subtotal = cart.apply_discount(0.33*10, 5)
        total_no_coupon = round2(subtotal + cart.shipping_fee(subtotal))
        assert self.c.total() == total_no_coupon
