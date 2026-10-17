import pytest
import cart

# ---- apply_discount ----
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),   # example from spec
        (100, 0, 100.0),    # no discount
        (50, 100, 0.0),     # full discount
    ],
)
def test_apply_discount_success(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# error conditions
@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 150])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---- bulk_discount_percent ----
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (9, 0),   # below 10
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

@pytest.mark.parametrize("quantity", [0, -5])
def test_bulk_discount_negative_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---- parse_coupon ----
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        (" SAVE30 ", 30),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVEXX", "INVALID", "SAVE0", "SAVE51", "SAVE-5", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---- shipping_fee ----
@pytest.mark.parametrize(
    "subtotal,member,fee",
    [
        (0, False, 60),
        (999.99, False, 60),
        (1000, False, 0),
        (2000, True, 30),
        (500, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, fee):
    assert cart.shipping_fee(subtotal, member) == fee

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative_subtotal(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Cart class ----
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_values(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    def test_add_item_new_and_existing(self):
        self.cart.add_item("apple", 2.5, 3)
        # after adding, quantity 3
        assert self.cart.items()["apple"] == 3
        # add same item with same price -> increase quantity
        self.cart.add_item("apple", 2.5, 2)
        assert self.cart.items()["apple"] == 5

    def test_add_item_invalid(self):
        with pytest.raises(ValueError):
            self.cart.add_item("banana", -1, 2)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 1.0, 0)

    def test_remove_item(self):
        self.cart.add_item("orange", 3.0, 4)
        # remove less than quantity
        self.cart.remove_item("orange", 2)
        assert self.cart.items()["orange"] == 2
        # removing remaining or more removes the item entirely
        self.cart.remove_item("orange", 5)
        assert "orange" not in self.cart.items()

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("pear")

    def test_subtotal_with_discounts(self):
        # add items to trigger bulk discounts
        self.cart.add_item("widget", 10.0, 5)   # 5 units => 5% discount
        self.cart.add_item("gadget", 20.0, 12)  # 12 units => 5% discount
        # calculate expected subtotal: each item after discount
        widget_price = 10.0 * 5 * (1 - 0.05)
        gadget_price = 20.0 * 12 * (1 - 0.05)
        expected_subtotal = round(widget_price + gadget_price, 2)
        assert self.cart.subtotal() == expected_subtotal

    def test_total_without_coupon_and_member(self):
        # simple case: subtotal < 1000, no member
        self.cart.add_item("book", 30.0, 2)  # 60
        # subtotal 60, no bulk discount
        assert self.cart.subtotal() == 60.0
        # total = 60 + shipping 60 = 120
        assert self.cart.total() == 120.0

    def test_total_with_coupon_and_member(self):
        # subtotal 200 with coupon 20% off
        self.cart.add_item("pen", 10.0, 20)  # 200 before discount
        # bulk discount for 20 units => 10%
        discounted = 200 * (1 - 0.10)
        # coupon reduces by 20%
        after_coupon = round(discounted * (1 - 0.20), 2)
        # shipping fee on after_coupon: member => half
        shipping = 30 if after_coupon < 1000 else 0
        expected_total = round(after_coupon + shipping, 2)
        assert self.cart.total(member=True, coupon="SAVE20") == expected_total
