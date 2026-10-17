import pytest
import cart

# ---- basic helpers --------------------------------------------------------
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50.5, 20, 40.4),  # rounding
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price,percent",
    [(-1, 10), (100, -5), (50, 105)],
)
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---- bulk discount -------------------------------------------------------
@pytest.mark.parametrize(
    "qty,expected",
    [
        (5, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
    ],
)
def test_bulk_discount(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -3, 2.5])
def test_bulk_discount_errors(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---- coupon parsing ------------------------------------------------------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save5", 5),
        ("  SaVe20 ", 20),
    ],
)
def test_parse_coupon(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAFe50", "DISCOUNT10", "SAVE-5", "SAVE51"])    
def test_parse_coupon_errors(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---- shipping fee --------------------------------------------------------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (1000, False, 0),
        (999.99, False, 60),
        (500, True, 30),
        (0, False, 60),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Cart class ----------------------------------------------------------
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_add_and_items(self):
        self.c.add_item("apple", 1.0, quantity=3)
        assert self.c.items() == {"apple": 3}
        # adding same item increases qty
        self.c.add_item("APPLE", 1.0, quantity=2)  # name case? should be exact
        assert self.c.items() == {"apple": 5}

    def test_add_errors(self):
        with pytest.raises(ValueError):
            self.c.add_item("banana", -1)
        with pytest.raises(ValueError):
            self.c.add_item("banana", 1, quantity=0)

    def test_remove_and_items(self):
        self.c.add_item("orange", 2.0, quantity=4)
        self.c.remove_item("orange", quantity=2)
        assert self.c.items() == {"orange": 2}
        self.c.remove_item("orange", quantity=2)  # remove all
        assert self.c.items() == {}

    def test_remove_errors(self):
        with pytest.raises(KeyError):
            self.c.remove_item("mango")

    def test_subtotal_no_discount(self):
        self.c.add_item("pear", 5.0, quantity=2)
        assert self.c.subtotal() == 10.0

    def test_subtotal_bulk_discount(self):
        # 12 items, bulk discount 5%
        self.c.add_item("widget", 20.0, quantity=12)
        expected = round(20.0*12 * 0.95, 2)
        assert self.c.subtotal() == expected

    def test_total_without_coupon(self):
        self.c.add_item("thing", 100.0, quantity=1)
        subtotal = 100.0
        shipping = cart.shipping_fee(subtotal)
        total_expected = round(subtotal + shipping, 2)
        assert self.c.total() == total_expected

    def test_total_with_coupon(self):
        self.c.add_item("thing", 200.0, quantity=1)
        subtotal = 200.0
        discounted = cart.apply_discount(subtotal, 10)  # 10% coupon
        shipping = cart.shipping_fee(discounted)
        total_expected = round(discounted + shipping, 2)
        assert self.c.total(coupon="SAVE10") == total_expected

    def test_total_errors(self):
        with pytest.raises(ValueError):
            self.c.total(coupon="BADCODE")

    def test_empty_cart_costs_zero(self):
        assert self.c.total() == 0.0
        assert self.c.subtotal() == 0.0

# ---- edge cases ---------------------------------------------------------
@pytest.mark.parametrize(
    "name,price,quantity",
    [("book", 12.99, 5), ("pen", 0.99, 200)],
)
def test_bulk_discount_in_total(name, price, quantity):
    c = cart.Cart()
    c.add_item(name, price, quantity)
    # compute expected subtotal
    bulk_pct = cart.bulk_discount_percent(quantity)
    expected_subtotal = round(price * quantity * (1 - bulk_pct/100), 2)
    assert c.subtotal() == expected_subtotal

# Run all tests with pytest via function (optional, not required in file)
PY
