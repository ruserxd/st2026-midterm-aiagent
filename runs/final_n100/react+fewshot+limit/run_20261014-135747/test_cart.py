import pytest
import cart

# Helper for expected discount application

def expected_discount(price, percent):
    return round(price * (1 - percent / 100), 2)

# Test apply_discount with valid inputs and error cases
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200.0, 15, 170.0),
        (100.0, 0, 100.0),
        (50.5, 100, 0.0),
        (123.45, 25.5, round(123.45 * 0.745, 2)),
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price,percent", [(-10, 20), (50, -5), (30, 105)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 2.5])
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        (" save5 ", 5),
        ("SaVe50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["", "ABC10", "SAVE0", "SAVE51", "save-5", "  ", None])
def test_parse_coupon_errors(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (500, True, 30),
        (999.99, False, 60),
        (1000, False, 0),
        (1500, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart functionality tests
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_initial_state(self):
        assert self.c.items() == {}
        assert self.c.subtotal() == 0.0
        assert self.c.total() == 0.0

    def test_add_item_new_and_increment(self):
        self.c.add_item("apple", 2.5, 3)
        assert self.c.items() == {"apple": 3}
        # adding same item with same price increases quantity
        self.c.add_item("apple", 2.5, 2)
        assert self.c.items() == {"apple": 5}

    def test_add_item_price_mismatch(self):
        self.c.add_item("banana", 1.0)
        with pytest.raises(ValueError):
            self.c.add_item("banana", 1.5)

    def test_add_item_invalid_parameters(self):
        with pytest.raises(ValueError):
            self.c.add_item("pear", -1, 2)
        with pytest.raises(ValueError):
            self.c.add_item("pear", 1, 0)
        with pytest.raises(ValueError):
            self.c.add_item("pear", 1, -3)

    def test_remove_item(self):
        self.c.add_item("orange", 0.75, 4)
        self.c.remove_item("orange", 2)
        assert self.c.items() == {"orange": 2}
        # remove remaining to delete item
        self.c.remove_item("orange", 2)
        assert self.c.items() == {}

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.c.remove_item("nonexistent")

    def test_subtotal_no_discount(self):
        self.c.add_item("pen", 1.2, 5)  # quantity <10, no bulk discount
        assert self.c.subtotal() == round(1.2 * 5, 2)

    def test_subtotal_with_bulk_discount(self):
        self.c.add_item("stapler", 15.0, 12)  # 5% discount
        expected = round(15.0 * 12 * (1 - 5 / 100), 2)
        assert self.c.subtotal() == expected

    def test_total_without_coupon_or_member(self):
        self.c.add_item("book", 20, 2)  # subtotal 40
        total = self.c.total()
        # subtotal 40 -> coupon none; shipping 60 added => 100.0
        assert total == round(40 + 60, 2)

    def test_total_with_coupon(self):
        self.c.add_item("notebook", 5, 10)  # subtotal 50 -> 5% discount => 47.5
        # coupon SAVE10 gives 10% off on 47.5 -> 42.75
        total = self.c.total(coupon="SAVE10")
        expected = round(42.75 + cart.shipping_fee(42.75), 2)
        assert total == expected

    def test_total_member_shipping(self):
        self.c.add_item("gadget", 200, 1)  # subtotal 200 -> no discount
        # member pays half shipping (30)
        total = self.c.total(member=True)
        expected = round(200 + cart.shipping_fee(200, True), 2)
        assert total == expected

    def test_total_invalid_coupon(self):
        with pytest.raises(ValueError):
            self.c.total(coupon="BADCODE")

    def test_total_empty_cart_no_shipping(self):
        # Cart already empty in setup; ensure no shipping fee added
        assert self.c.total() == 0.0
