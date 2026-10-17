import pytest
import cart

# --- apply_discount ---
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (100, 100, 0.0),
])
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --- bulk_discount_percent ---
@pytest.mark.parametrize("quantity,expected", [
    (9, 0), (10, 5), (49, 5), (50, 10), (99, 10), (100, 15), (150, 15)
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --- parse_coupon ---
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    (" save20 ", 20),
    ("SaVe5", 5),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "DISCOUNT10", "", "save-5", "save5a"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee ---
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (500, True, 30),
    (999.99, False, 60),
    (1000, False, 0),
    (1500, True, 0)
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --- Cart class tests ---
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_add_and_items(self):
        self.c.add_item("apple", 1.0, 3)
        self.c.add_item("banana", 0.5, 2)
        assert self.c.items() == {"apple": 3, "banana": 2}

    def test_add_existing_increases_quantity(self):
        self.c.add_item("orange", 1.5, 2)
        self.c.add_item("orange", 1.5, 4)
        assert self.c.items() == {"orange": 6}

    def test_add_existing_wrong_price_raises(self):
        self.c.add_item("pear", 2.0, 1)
        with pytest.raises(ValueError):
            self.c.add_item("pear", 3.0, 1)

    @pytest.mark.parametrize("name,quantity", [("kiwi", 0), ("mango", -1)])
    def test_add_invalid_quantity(self, name, quantity):
        with pytest.raises(ValueError):
            self.c.add_item(name, 2.5, quantity)

    @pytest.mark.parametrize("name,quantity", [("apple", 1), ("banana", -2)])
    def test_remove_existing(self, name, quantity):
        self.c.add_item(name, 0.8, 3)
        if quantity > 0:
            self.c.remove_item(name, quantity)
            expected_qty = 3 - quantity
            if expected_qty <= 0:
                assert name not in self.c.items()
            else:
                assert self.c.items()[name] == expected_qty

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.c.remove_item("nonexistent", 1)

    def test_subtotal_with_bulk_discount(self):
        # 10 units of item gives 5% discount
        self.c.add_item("pen", 2.0, 10)
        assert self.c.subtotal() == round(2.0*10*(1-0.05), 2)

    def test_total_without_coupon_or_member(self):
        self.c.add_item("book", 15.0, 1)
        expected = 15.0 + cart.shipping_fee(15.0)
        assert self.c.total() == round(expected, 2)

    def test_total_with_member_no_shipping_if_free(self):
        self.c.add_item("expensive", 1200.0, 1)
        # subtotal >=1000 so shipping free even without member flag
        assert self.c.total(member=True) == 1200.0

    def test_total_with_coupon_and_member(self):
        self.c.add_item("widget", 20.0, 5)  # no bulk discount
        coupon_percent = cart.parse_coupon("SAVE10")
        subtotal_after_coupon = round(20.0*5*(1-coupon_percent/100), 2)
        shipping = cart.shipping_fee(subtotal_after_coupon, member=True)
        total_expected = round(subtotal_after_coupon + shipping, 2)
        assert self.c.total(member=True, coupon="SAVE10") == total_expected

    def test_total_empty_cart(self):
        assert self.c.total() == 0.0

    def test_total_invalid_coupon_raises(self):
        self.c.add_item("item", 5.0, 1)
        with pytest.raises(ValueError):
            self.c.total(coupon="BADCODE")
