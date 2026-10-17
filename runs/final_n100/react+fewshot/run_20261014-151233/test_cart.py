import pytest
import cart

# Helper to format floats

def round2(x):
    return round(float(x), 2)

# Tests for apply_discount
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# Invalid price or percent
@pytest.mark.parametrize("price,percent", [
    (-1, 10),
    (100, -5),
    (100, 150),
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent
@pytest.mark.parametrize("quantity,percent", [
    (1, 0),
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(quantity, percent):
    assert cart.bulk_discount_percent(quantity) == percent

# invalid quantity
@pytest.mark.parametrize("quantity", [0, -5, 3.5])
def test_bulk_discount_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    ("save25", 25),
    (" SAVE50 ", 50),
])
def test_parse_coupon(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", [
    "SAVE0",
    "SAVExx",
    "WRONG10",
    "SAVE51",
    "",
])
def test_parse_coupon_errors(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee
@pytest.mark.parametrize("subtotal,member,result", [
    (0, False, 60),
    (999.99, True, 30),
    (1000, False, 0),
    (1500, True, 0),
])
def test_shipping_fee(subtotal, member, result):
    assert cart.shipping_fee(subtotal, member) == result

@pytest.mark.parametrize("subtotal", [-10, -1.5])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart class tests
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_empty_cart_subtotal_and_total(self):
        assert self.c.subtotal() == 0.0
        assert self.c.total() == 0.0

    def test_add_item_new(self):
        self.c.add_item("apple", 1.00, 3)
        assert self.c.items() == {"apple": 3}
        # subtotal with no discount yet
        assert self.c.subtotal() == round2(3 * 1.0)

    def test_add_item_existing_same_price(self):
        self.c.add_item("banana", 0.5, 2)
        self.c.add_item("banana", 0.5, 3)
        assert self.c.items() == {"banana": 5}
        assert self.c.subtotal() == round2(5 * 0.5)

    def test_add_item_existing_different_price_error(self):
        self.c.add_item("cherry", 0.75, 1)
        with pytest.raises(ValueError):
            self.c.add_item("cherry", 0.80, 2)

    def test_remove_item_partial(self):
        self.c.add_item("date", 2.0, 4)
        self.c.remove_item("date", 2)
        assert self.c.items() == {"date": 2}

    def test_remove_item_exact(self):
        self.c.add_item("egg", 1.5, 3)
        self.c.remove_item("egg", 3)
        assert self.c.items() == {}

    def test_remove_item_more_than_exists(self):
        self.c.add_item("fig", 0.6, 2)
        self.c.remove_item("fig", 5)
        assert self.c.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.c.remove_item("grape", 1)

    def test_bulk_discount_in_subtotal(self):
        # 10 items -> 5% discount on that line
        self.c.add_item("honey", 2.0, 10)
        expected = round2(10 * 2.0 * (1 - 0.05))
        assert self.c.subtotal() == expected

    def test_total_with_coupon_and_shipping(self):
        # Add items to have subtotal >1000 for free shipping
        self.c.add_item("icecream", 200, 6)  # 1200 before discount
        # coupon 20%
        total = self.c.total(coupon="SAVE20")
        # After coupon: 1200 * 0.8 = 960 -> shipping 60
        expected = round2(960 + 60)
        assert total == expected

    def test_total_member_shipping_half(self):
        self.c.add_item("juice", 10, 5)  # subtotal 50
        total = self.c.total(member=True)
        # no coupon: shipping 30
        expected = round2(50 + 30)
        assert total == expected

    def test_total_no_shipping_when_free(self):
        self.c.add_item("kiosk", 200, 6)  # subtotal 1200 >1000
        total = self.c.total()
        assert total == round2(1200.0)

    def test_total_invalid_coupon_raises(self):
        with pytest.raises(ValueError):
            self.c.total(coupon="WRONG")
