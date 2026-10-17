import pytest
import cart

# ---------- apply_discount ----------

@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
        (123.45, 33, round(123.45 * 0.67, 2)),
    ],
)
def test_apply_discount_success(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize(
    "price,percent",
    [(-10, 20), (50, -5), (60, 105)],
)
def test_apply_discount_invalid_args(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------

@pytest.mark.parametrize(
    "qty,expected",
    [
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (250, 15),
    ],
)
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize(
    "qty",
    [0, -1, 3.5],
)
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- parse_coupon ----------

@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save25", 25),
        ("   SaVe50   ", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    ["SAVe0", "SAVE51", "NOTC10", "100", "", "save-5", "SAVEabc"],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------

@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (999.99, True, 30),
        (1000, False, 0),
        (1500, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-10, -1],
)
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ----------

class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    # add_item and items
    def test_add_and_items(self):
        self.c.add_item("apple", 1.0, 3)
        self.c.add_item("banana", 0.5)
        # Adding more apples increases quantity
        self.c.add_item("apple", 1.0, 2)
        items = self.c.items()
        assert items == {"apple": 5, "banana": 1}
        # Ensure returned dict is a copy
        items["apple"] = 99
        assert self.c.items()["apple"] == 5

    def test_add_item_invalid_price_or_qty(self):
        with pytest.raises(ValueError):
            self.c.add_item("orange", -1.0, 2)
        with pytest.raises(ValueError):
            self.c.add_item("orange", 1.0, 0)
        with pytest.raises(ValueError):
            self.c.add_item("orange", 1.0, 3.5)

    def test_add_item_price_mismatch(self):
        self.c.add_item("cherry", 2.0, 1)
        with pytest.raises(ValueError):
            self.c.add_item("cherry", 3.0, 1)

    # remove_item
    def test_remove_item(self):
        self.c.add_item("pear", 0.8, 4)
        self.c.remove_item("pear", 2)
        assert self.c.items()["pear"] == 2
        self.c.remove_item("pear", 2)
        assert "pear" not in self.c.items()

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.c.remove_item("nonexistent", 1)

    # subtotal calculation
    def test_subtotal_basic(self):
        self.c.add_item("widget", 10.0, 5)   # qty 5 => 5% discount
        expected = round(10.0 * 5 * (1 - 0.05), 2)
        assert self.c.subtotal() == expected

    def test_subtotal_bulk_discounts(self):
        # 12 units -> 5% discount, 55 units -> 10%, 120 units ->15%
        self.c.add_item("a", 1.0, 12)
        self.c.add_item("b", 2.0, 55)
        self.c.add_item("c", 3.0, 120)
        total = (
            round(1.0 * 12 * 0.95, 2) +
            round(2.0 * 55 * 0.90, 2) +
            round(3.0 * 120 * 0.85, 2)
        )
        assert self.c.subtotal() == round(total, 2)

    def test_subtotal_empty(self):
        assert self.c.subtotal() == 0

    # total calculation with coupon and shipping
    def test_total_with_coupon_and_shipping(self):
        # items: 3 units of price 100 => no bulk discount
        self.c.add_item("expensive", 100.0, 3)
        subtotal = round(100 * 3, 2)  # 300
        coupon_percent = cart.parse_coupon("SAVE10")
        after_coupon = round(subtotal * (1 - coupon_percent / 100), 2)
        shipping = cart.shipping_fee(after_coupon, member=False)
        expected_total = round(after_coupon + shipping, 2)
        assert self.c.total(coupon="SAVE10") == expected_total

    def test_total_member_shipping(self):
        self.c.add_item("cheap", 1.0, 20)  # 5% bulk discount: 19.0
        subtotal = round(1.0 * 20 * 0.95, 2)
        shipping = cart.shipping_fee(subtotal, member=True)
        expected_total = round(subtotal + shipping, 2)
        assert self.c.total(member=True) == expected_total

    def test_total_invalid_coupon(self):
        self.c.add_item("item", 10.0, 1)
        with pytest.raises(ValueError):
            self.c.total(coupon="BADCODE")

    def test_total_empty_cart(self):
        assert self.c.total() == 0
