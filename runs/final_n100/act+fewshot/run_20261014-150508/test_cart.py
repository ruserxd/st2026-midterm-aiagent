import pytest
import cart

# ---------- helpers for parsing expected discounts and coupons ----------
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),          # normal discount
        (100, 0, 100.0),           # no discount
        (50, 100, 0.0),            # full free
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# ---- test validation errors for apply_discount -----------------------
@pytest.mark.parametrize("price,percent", [(-1, 10), (50, -5), (50, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent -------------------------------------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (5, 0),   # <10
        (10, 5),  # >=10 <50
        (49, 5),
        (50, 10), # >=50 <100
        (99, 10),
        (100, 15),# >=100
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 3.7])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon -----------------------------------------------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save25 ", 25),
        ("   SaVe50  ", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["", "ABCD", "SAVE0", "SAVE51", " SAVE-1 ", "1234", None])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee -----------------------------------------------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (1200, False, 0),   # free over 1000
        (999.99, True, 30), # half for members
        (999.99, False, 60),# full fee
        (0, True, 30),      # member even with empty cart
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class tests ------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    # adding items -------------------------------------
    @pytest.mark.parametrize("name,unit_price,quantity", [
        ("apple", 100, 1),
        ("banana", 50.5, 3),
    ])
    def test_add_item(self, name, unit_price, quantity):
        self.cart.add_item(name, unit_price, quantity)
        assert self.cart.items()[name] == quantity

    def test_add_existing_increases_quantity_and_same_price(self):
        self.cart.add_item("apple", 100, 1)
        self.cart.add_item("apple", 100, 2)
        assert self.cart.items()["apple"] == 3

    def test_add_existing_different_price_raises(self):
        self.cart.add_item("apple", 100, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("apple", 90, 2)

    @pytest.mark.parametrize("unit_price,quantity", [(-10, 1), (5, 0)])
    def test_add_invalid(self, unit_price, quantity):
        with pytest.raises(ValueError):
            self.cart.add_item("bad", unit_price, quantity)

    # removing items ---------------------------------
    def test_remove_item_shows_decrease_and_removal(self):
        self.cart.add_item("pear", 200, 3)
        self.cart.remove_item("pear", 2)
        assert self.cart.items()["pear"] == 1
        self.cart.remove_item("pear", 1)  # should remove completely
        assert "pear" not in self.cart.items()

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nothing", 1)

    # subtotal calculation ---------------------------------
    def test_subtotal_with_bulk_discount_and_rounding(self):
        # apple: 100 each, qty 5 -> no bulk discount
        self.cart.add_item("apple", 100, 5)   # 500
        # banana: 50 each, qty 12 -> 5% bulk discount
        self.cart.add_item("banana", 50, 12)  # base 600, 5% off => 570
        expected = round(500 + 570, 2)
        assert self.cart.subtotal() == expected

    def test_subtotal_empty_cart(self):
        assert self.cart.subtotal() == 0

    # total calculation ---------------------------------
    def test_total_no_coupon_and_nonmember(self):
        self.cart.add_item("item", 100, 1)
        subtotal = self.cart.subtotal()
        shipping = cart.shipping_fee(subtotal, member=False)
        expected = round(subtotal + shipping, 2)
        assert self.cart.total(member=False) == expected

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("item", 200, 1)
        subtotal = self.cart.subtotal()
        coupon_percent = cart.parse_coupon("SAVE20")
        after_coupon = round(subtotal * (1 - coupon_percent / 100), 2)
        shipping = cart.shipping_fee(after_coupon, member=True)
        expected = round(after_coupon + shipping, 2)
        assert self.cart.total(member=True, coupon="SAVE20") == expected

    def test_total_empty_cart(self):
        assert self.cart.total() == 0

    def test_total_invalid_coupon_raises(self):
        self.cart.add_item("item", 100, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")
