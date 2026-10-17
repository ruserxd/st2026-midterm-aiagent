import pytest
import cart

# helper to round expected values

def round2(x):
    return round(float(x), 2)

# ---------- apply_discount ----------
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200.0, 15, 170.0),            # example from spec
        (100.0, 0, 100.0),             # no discount
        (50.0, 100, 0.0),              # full discount
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price, percent",
    [(-10, 5), (50, -1), (30, 110)],
)
def test_apply_discount_invalid_args(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (5, 0),      # below 10
        (10, 5),     # >=10 but <50
        (49, 5),     # just below 50
        (50, 10),    # >=50 but <100
        (99, 10),
        (100, 15),   # >=100
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 3.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save20", 20),          # case‑insensitive
        ("  SaVe30  ", 30),      # whitespace stripped
        ("SAVE50", 50),          # max allowed
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAV10", "SAVE0", "SAVE51", "SAVEabc", ""] )
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (500.0, False, 60),   # <1000, non‑member
        (500.0, True, 30),    # <1000, member
        (1000.0, False, 0),   # exactly 1000 free
        (2000.0, True, 0),    # >1000 free
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -50])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ----------
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    # add_item and items
    def test_add_and_items(self):
        self.c.add_item("apple", 0.5, 4)
        self.c.add_item("banana", 0.2, 10)
        assert self.c.items() == {"apple": 4, "banana": 10}

    def test_add_existing_increases_quantity(self):
        self.c.add_item("orange", 1.0, 3)
        self.c.add_item("orange", 1.0, 2)
        assert self.c.items() == {"orange": 5}

    @pytest.mark.parametrize(
        "name, unit_price, quantity",
        [
            ("pear", -0.1, 1),      # negative price
            ("peach", 0.3, 0),      # zero quantity
            ("plum", 0.4, -2),      # negative quantity
            ("melon", 0.5, 1.5),    # non‑int quantity
        ],
    )
    def test_add_item_invalid(self, name, unit_price, quantity):
        with pytest.raises(ValueError):
            self.c.add_item(name, unit_price, quantity)

    def test_add_item_unit_price_mismatch(self):
        self.c.add_item("kiwi", 0.6, 2)
        with pytest.raises(ValueError):
            # same name but different price
            self.c.add_item("kiwi", 0.8, 1)

    # remove_item
    def test_remove_item(self):
        self.c.add_item("grape", 0.2, 5)
        self.c.remove_item("grape", 3)
        assert self.c.items() == {"grape": 2}
        self.c.remove_item("grape", 2)  # should remove completely
        assert "grape" not in self.c.items()

    def test_remove_item_not_in_cart(self):
        with pytest.raises(KeyError):
            self.c.remove_item("mango", 1)

    @pytest.mark.parametrize("quantity", [0, -3])
    def test_remove_item_invalid_quantity(self, quantity):
        self.c.add_item("fig", 0.5, 2)
        with pytest.raises(ValueError):
            # remove expects positive integer; negative or zero is invalid
            self.c.remove_item("fig", quantity)

    # subtotal and bulk discounts
    def test_subtotal_no_discount(self):
        self.c.add_item("bread", 1.5, 3)   # <10 units -> no discount
        assert round2(self.c.subtotal()) == round2(1.5 * 3)

    def test_subtotal_with_bulk_discount(self):
        self.c.add_item("cheese", 4.0, 12)  # >=10 -> 5% discount on this item
        expected = 4.0 * 12 * (1 - 0.05)
        assert round2(self.c.subtotal()) == round2(expected)

    def test_subtotal_multiple_items(self):
        self.c.add_item("milk", 3.0, 8)     # <10 -> no discount
        self.c.add_item("nuts", 10.0, 55)   # >=50 -> 10% discount
        milk_total = 3.0 * 8
        nuts_total = 10.0 * 55 * (1 - 0.10)
        assert round2(self.c.subtotal()) == round2(milk_total + nuts_total)

    def test_subtotal_empty_cart(self):
        assert self.c.subtotal() == 0

    # total with coupon and shipping
    def test_total_no_coupon_no_member(self):
        self.c.add_item("pen", 1.0, 10)     # bulk discount 5%
        subtotal = 1.0 * 10 * (1 - 0.05)
        expected = round2(subtotal + cart.shipping_fee(subtotal))
        assert round2(self.c.total()) == expected

    def test_total_with_coupon_and_member(self):
        self.c.add_item("book", 20.0, 5)   # no bulk discount
        subtotal = 20.0 * 5
        coupon_percent = cart.parse_coupon("SAVE10")
        after_coupon = subtotal * (1 - coupon_percent / 100)
        expected = round2(after_coupon + cart.shipping_fee(after_coupon, member=True))
        assert round2(self.c.total(member=True, coupon="SAVE10")) == expected

    def test_total_invalid_coupon(self):
        self.c.add_item("item", 5.0, 1)
        with pytest.raises(ValueError):
            self.c.total(coupon="BADCODE")

    def test_total_empty_cart_no_shipping(self):
        assert self.c.total() == 0

    def test_total_edge_shopping_fee_free(self):
        # subtotal after coupon >=1000 -> shipping free
        self.c.add_item("expensive", 200.0, 6)   # 1200 total before discount
        subtotal = 200 * 6
        percent = cart.bulk_discount_percent(6)  # no bulk discount
        after_coupon = subtotal * (1 - 20 / 100)  # assume coupon 20%
        assert after_coupon >= 1000
        expected = round2(after_coupon + cart.shipping_fee(after_coupon))
        # shipping fee should be 0 because after_coupon >= 1000
        assert cart.shipping_fee(after_coupon) == 0
        assert round2(self.c.total(coupon="SAVE20")) == expected
