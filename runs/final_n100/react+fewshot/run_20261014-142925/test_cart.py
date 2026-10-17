import pytest
import cart

# apply_discount
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# bulk_discount_percent
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (200, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 3.2])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save5", 5),
        ("  SaVe20 ", 20),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVEE10", "SAVE0", "SAVE51", "1234", ""] )
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee
@pytest.mark.parametrize(
    "subtotal, member, expected",
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

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart class tests
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_item_new(self):
        self.cart.add_item("Apple", 2.5, 3)
        assert self.cart.items() == {"Apple": (2.5, 3)}

    def test_add_item_existing_same_price(self):
        self.cart.add_item("Banana", 1.0, 2)
        self.cart.add_item("Banana", 1.0, 4)
        assert self.cart.items() == {"Banana": (1.0, 6)}

    def test_add_item_existing_different_price(self):
        self.cart.add_item("Orange", 2.0, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("Orange", 3.0, 1)

    @pytest.mark.parametrize("name, quantity", [("Apple", -1), ("Banana", 0)])
    def test_add_invalid(self, name, quantity):
        with pytest.raises(ValueError):
            self.cart.add_item(name, 5.0, quantity)

    def test_remove_item_partial(self):
        self.cart.add_item("Grapes", 3.0, 5)
        self.cart.remove_item("Grapes", 2)
        assert self.cart.items() == {"Grapes": (3.0, 3)}

    def test_remove_item_exact(self):
        self.cart.add_item("Mango", 4.0, 2)
        self.cart.remove_item("Mango", 2)
        assert "Mango" not in self.cart.items()

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("NonExistent", 1)

    def test_subtotal(self):
        self.cart.add_item("Pen", 1.2, 3)  # 3.6
        self.cart.add_item("Notebook", 2.5, 2)  # 5.0
        assert self.cart.subtotal() == 8.6

    def test_total_no_discount(self):
        self.cart.add_item("Pen", 1.0, 2)
        assert self.cart.total() == 2.0

    def test_total_with_bulk_discount(self):
        self.cart.add_item("Sticker", 0.5, 60)  # bulk discount 10%
        expected = 0.5 * 60 * 0.9
        assert self.cart.total() == expected

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("Book", 30.0, 1)
        total_before = 30.0
        # member shipping half, subtotal <1000 => fee 30 -> member 15
        # coupon SAVE10 gives 10% off after discounts? Assume applied to item total before shipping
        expected_items = total_before * 0.9  # apply 10%
        shipping = 15
        assert self.cart.total(member=True, coupon="SAVE10") == expected_items + shipping
