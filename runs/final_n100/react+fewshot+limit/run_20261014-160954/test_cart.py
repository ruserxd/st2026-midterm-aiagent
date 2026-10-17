import pytest
import cart

# ----- apply_discount -----
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),          # example from spec
        (100, 0, 100.0),           # no discount
        (50, 100, 0.0),            # full discount
    ],
)
def test_apply_discount_success(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# boundary and error cases
@pytest.mark.parametrize(
    "price",
    [-1, -10],
)
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize(
    "percent",
    [-5, 101, 200],
)
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ----- bulk_discount_percent -----
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (5, 0),   # less than 10
        (10, 5),  # threshold 10
        (49, 5),  # just below 50
        (50, 10), # threshold 50
        (99, 10), # just below 100
        (100, 15),# threshold 100
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -5, 3.5],
)
def test_bulk_discount_percent_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ----- parse_coupon -----
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        (" SAVE30 ", 30),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    ["SAVE0", "SAVE51", "INVALID", "SAVEXX", "   "] ,
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ----- shipping_fee -----
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, 60),
        (500, True, 30),
        (1000, False, 0),
        (1500, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-1, -100],
)
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ----- Cart class -----
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initially_empty(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    # adding items
    def test_add_item_new(self):
        self.cart.add_item("apple", 2.5, quantity=3)
        assert self.cart.items() == {"apple": 3}
        # subtotal without discount: 7.5; no bulk discount for qty<10
        assert self.cart.subtotal() == 7.5

    def test_add_item_existing_same_price(self):
        self.cart.add_item("banana", 1.0, quantity=2)
        self.cart.add_item("banana", 1.0, quantity=4)
        assert self.cart.items() == {"banana": 6}
        # subtotal: 6*1.0 = 6.0
        assert self.cart.subtotal() == 6.0

    def test_add_item_same_name_different_price_raises(self):
        self.cart.add_item("pear", 3.0, quantity=1)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 4.0, quantity=1)

    # error cases for add_item
    def test_add_item_negative_price(self):
        with pytest.raises(ValueError):
            self.cart.add_item("orange", -2.0, quantity=1)

    def test_add_item_invalid_quantity(self):
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 2.0, quantity=-3)

    # removing items
    def test_remove_item_partial_and_full(self):
        self.cart.add_item("mango", 5.0, quantity=4)
        self.cart.remove_item("mango", quantity=1)  # qty now 3
        assert self.cart.items() == {"mango": 3}
        self.cart.remove_item("mango", quantity=3)  # removed
        assert self.cart.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("kiwi", quantity=1)

    # subtotal bulk discount logic
    def test_subtotal_bulk_discount(self):
        # 12 units triggers 5% bulk discount
        self.cart.add_item("tshirt", 20.0, quantity=12)
        expected = 20.0 * 12 * (1 - 0.05)  # 240 * 0.95
        assert pytest.approx(self.cart.subtotal(), rel=1e-9) == round(expected, 2)

    # total with coupon and shipping
    def test_total_with_coupon_and_shipping(self):
        self.cart.add_item("widget", 30.0, quantity=10)  # qty>=10 => 5% bulk discount
        subtotal = 30.0 * 10 * 0.95  # 285.0
        coupon_percent = cart.parse_coupon("SAVE20")  # 20%
        after_coupon = subtotal * (1 - coupon_percent / 100)
        shipping = cart.shipping_fee(after_coupon, member=True)  # half fee
        expected_total = after_coupon + shipping
        assert pytest.approx(self.cart.total(member=True, coupon="SAVE20"), rel=1e-9) == round(expected_total, 2)

    def test_total_empty_cart_no_shipping(self):
        assert self.cart.total() == 0.0
