import pytest
import cart

# Helper for rounding in tests

def round2(x):
    return round(float(x), 2)

# ---------- apply_discount -------------------------------------------------
@pytest.mark.parametrize("price, percent, expected", [
    (200, 15, 170.0),          # example from spec
    (100, 0, 100.0),           # no discount
    (50, 100, 0.0),            # full discount
])
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# error cases for apply_discount
@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_price_negative(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_percent_invalid(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent -------------------------------------------
@pytest.mark.parametrize("quantity, expected", [
    (9, 0),   # below 10
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 3.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(int(quantity))

# ---------- parse_coupon -----------------------------------------------------
@pytest.mark.parametrize("code, expected", [
    ("SAVE10", 10),
    ("save20 ", 20),   # case-insensitive and whitespace
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "WRONG", "SAVExx", "10SAVE"]) 
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee -----------------------------------------------------
@pytest.mark.parametrize("subtotal, member, expected", [
    (0, False, 60),          # below 1000
    (999.99, True, 30),      # member gets half
    (1000, False, 0),        # free shipping threshold
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart tests ------------------------------------------------------
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    # add_item and items
    def test_add_and_items(self):
        self.c.add_item("apple", 2.0, 3)
        assert self.c.items() == {"apple": 3}
        # adding same item increases quantity
        self.c.add_item("apple", 2.0, 2)
        assert self.c.items() == {"apple": 5}

    def test_add_existing_different_price(self):
        self.c.add_item("banana", 1.5)
        with pytest.raises(ValueError):
            # same name, different unit price
            self.c.add_item("banana", 2.0)

    def test_add_invalid_unit_price_or_quantity(self):
        with pytest.raises(ValueError):
            self.c.add_item("pear", -1.0)
        with pytest.raises(ValueError):
            self.c.add_item("pear", 1.0, 0)

    # remove_item
    def test_remove_partial_and_full(self):
        self.c.add_item("orange", 3.0, 4)
        self.c.remove_item("orange", 2)
        assert self.c.items() == {"orange": 2}
        self.c.remove_item("orange", 2)
        assert self.c.items() == {}

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.c.remove_item("mango", 1)

    # subtotal calculation with bulk discount
    def test_subtotal_no_discount(self):
        self.c.add_item("itemA", 10.0, 5)  # quantity < 10 => no discount
        assert round2(self.c.subtotal()) == 50.0

    def test_subtotal_with_bulk_discount(self):
        # quantity 12 => bulk discount 5%
        self.c.add_item("itemB", 20.0, 12)
        expected = 20.0 * 12 * (1 - 0.05)  # 240 * 0.95
        assert round2(self.c.subtotal()) == round2(expected)

    def test_subtotal_empty_cart(self):
        assert self.c.subtotal() == 0

    # total with coupon and shipping
    def test_total_no_coupon_or_shipping(self):
        # subtotal $500 -> shipping 60, no coupon
        self.c.add_item("itemC", 100.0, 5)
        amount = self.c.total()
        expected_subtotal = 500.0
        expected_shipping = cart.shipping_fee(expected_subtotal)
        assert round2(amount) == round2(expected_subtotal + expected_shipping)

    def test_total_with_coupon_and_member(self):
        # subtotal $1200 -> free shipping, coupon SAVE10 reduces by 10%
        self.c.add_item("expensive", 200.0, 6)
        amount = self.c.total(member=True, coupon="SAVE10")
        subtotal = self.c.subtotal()
        discounted = cart.apply_discount(subtotal, 10)  # apply_coupon
        shipping = cart.shipping_fee(discounted, member=True)
        expected = round2(discounted + shipping)
        assert round2(amount) == expected

    def test_total_invalid_coupon(self):
        self.c.add_item("item", 50.0, 1)
        with pytest.raises(ValueError):
            self.c.total(coupon="BADCODE")

    def test_total_empty_cart(self):
        assert self.c.total() == 0
