import pytest
import cart

# Helper: round helper

def round2(x):
    return round(float(x), 2)

############################
# apply_discount
############################
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),          # example from spec
    (100, 0, 100.0),           # no discount
    (50, 100, 0.0),            # full discount
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == round2(result)

@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_price_negative(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 20)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_percent_invalid(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

############################
# bulk_discount_percent
############################
@pytest.mark.parametrize("qty,expected", [
    (9, 0),      # below 10
    (10, 5),     # threshold
    (49, 5),     # just below 50
    (50, 10),    # threshold
    (99, 10),    # just below 100
    (100, 15),   # threshold
    (150, 15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -1, 5.5])
def test_bulk_discount_percent_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(int(qty)) if isinstance(qty, int) else cart.bulk_discount_percent(qty)

############################
# parse_coupon
############################
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVEX", "SAVE0", "SAVE51", "BAD10", ""] )
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

############################
# shipping_fee
############################
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (500, True, 30),
    (1000, False, 0),
    (999.99, False, 60),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

############################
# Cart class tests
############################
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_initially_empty(self):
        assert self.c.items() == {}
        assert self.c.subtotal() == 0.0
        assert self.c.total() == 0.0

    def test_add_item_new(self):
        self.c.add_item("apple", 2.5, quantity=3)
        assert self.c.items() == {"apple": 3}
        # subtotal with no bulk discount: 2.5*3 = 7.5
        assert self.c.subtotal() == round2(7.5)

    def test_add_item_existing_same_price(self):
        self.c.add_item("banana", 1.0, quantity=2)
        self.c.add_item("banana", 1.0, quantity=3)
        assert self.c.items() == {"banana": 5}
        assert self.c.subtotal() == round2(5 * 1.0)  # no bulk discount yet

    def test_add_item_existing_different_price(self):
        self.c.add_item("orange", 1.5, quantity=2)
        with pytest.raises(ValueError):
            self.c.add_item("orange", 2.0, quantity=1)

    def test_remove_item_partial(self):
        self.c.add_item("mango", 3.0, quantity=4)
        self.c.remove_item("mango", quantity=2)
        assert self.c.items() == {"mango": 2}
        assert self.c.subtotal() == round2(2 * 3.0)

    def test_remove_item_to_zero(self):
        self.c.add_item("peach", 4.0, quantity=1)
        self.c.remove_item("peach")
        assert self.c.items() == {}
        assert self.c.subtotal() == 0.0

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.c.remove_item("nonexist", quantity=1)

    def test_bulk_discount_in_subtotal(self):
        # 12 units -> bulk discount 5%
        self.c.add_item("grape", 10.0, quantity=12)
        expected = round2(12 * 10.0 * (1 - 0.05))
        assert self.c.subtotal() == expected

    def test_total_with_coupon_and_shipping(self):
        # Add items to reach subtotal > 1000 for free shipping after coupon
        self.c.add_item("widget", 200.0, quantity=6)  # 1200 total
        # apply 10% coupon -> 1080
        tot = self.c.total(coupon="SAVE10")
        assert tot == round2(1080.0)  # free shipping because >=1000 after coupon

    def test_total_with_shipping_and_member(self):
        self.c.add_item("gadget", 50.0, quantity=5)  # 250 total
        tot = self.c.total(member=True)
        # subtotal 250, no coupon, shipping 30 -> 280
        assert tot == round2(250 + 30)

    def test_total_empty_cart(self):
        assert self.c.total() == 0.0

    def test_invalid_coupon_in_total_raises(self):
        with pytest.raises(ValueError):
            self.c.total(coupon="BADCODE")

# End of tests
