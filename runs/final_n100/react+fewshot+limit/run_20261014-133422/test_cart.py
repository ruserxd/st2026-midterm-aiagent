import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---- apply_discount -------------------------------------------------
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200.0, 15, 170.00),
        (100.0, 0, 100.00),
        (50.0, 100, 0.00),
        (123.45, 25, round(123.45 * 0.75, 2)),
    ],
)
def test_apply_discount_valid(price, percent, result):
    assert apply_discount(price, percent) == result

@pytest.mark.parametrize(
    "price,percent",
    [(-1, 10), (50, -5), (50, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---- bulk_discount_percent -------------------------------------------
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
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -5, 2.3],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---- parse_coupon -----------------------------------------------------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20 ", 20),
        ("  SaVe5", 5),
        ("SaVe50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    ["SAVE0", "SAVE51", "INVALID", "123", "SAVEX5", " SAVE10X "],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---- shipping_fee -----------------------------------------------------
@pytest.mark.parametrize(
    "subtotal,member,result",
    [
        (0.0, False, 60),
        (999.99, True, 30),
        (1000.0, False, 0),
        (1200.0, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, result):
    assert shipping_fee(subtotal, member) == result

@pytest.mark.parametrize(
    "subtotal",
    [-1, -100],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---- Cart -------------------------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = Cart()

    def test_initial_cart_is_empty(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.00
        assert self.cart.total() == 0.00

    # add_item tests
    @pytest.mark.parametrize(
        "name,unit_price,quantity",
        [
            ("apple", 1.5, 3),
            ("banana", 0.99, 10),
        ],
    )
    def test_add_item(self, name, unit_price, quantity):
        self.cart.add_item(name, unit_price, quantity)
        assert self.cart.items()[name] == quantity

    @pytest.mark.parametrize(
        "existing_name,unit_price,new_qty",
        [
            ("apple", 2.0, 5),
        ],
    )
    def test_add_item_increases_quantity(self, existing_name, unit_price, new_qty):
        self.cart.add_item(existing_name, unit_price, 2)
        self.cart.add_item(existing_name, unit_price, new_qty)
        assert self.cart.items()[existing_name] == 2 + new_qty

    def test_add_item_invalid_price_or_quantity(self):
        with pytest.raises(ValueError):
            self.cart.add_item("pear", -1.0, 3)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 1.0, 0)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 1.0, 2.5)

    def test_add_item_price_mismatch(self):
        self.cart.add_item("orange", 1.0, 4)
        with pytest.raises(ValueError):
            # same name but different unit price
            self.cart.add_item("orange", 1.50, 2)

    # remove_item tests
    def test_remove_item(self):
        self.cart.add_item("apple", 1.0, 5)
        self.cart.remove_item("apple", 2)
        assert self.cart.items()["apple"] == 3

    def test_remove_item_more_than_exists(self):
        self.cart.add_item("apple", 1.0, 3)
        # Removing more than present should leave quantity zero (remove entry)
        self.cart.remove_item("apple", 5)
        assert "apple" not in self.cart.items()

    def test_remove_nonexistent_item(self):
        # Removing an item that isn't in the cart does nothing
        self.cart.remove_item("banana", 1)
        assert self.cart.items() == {}

    # subtotal calculation tests
    def test_subtotal_no_bulk_discount(self):
        self.cart.add_item("toy", 10.0, 4)  # <10 units -> no discount
        assert self.cart.subtotal() == round(10.0 * 4, 2)

    def test_subtotal_with_bulk_discounts(self):
        # quantity 12 => 5% bulk discount
        self.cart.add_item("book", 20.0, 12)
        expected = round(20.0 * 12 * (1 - 0.05), 2)
        assert self.cart.subtotal() == expected
        # quantity 55 => 10%
        self.cart.add_item("pen", 5.0, 55)
        expected += round(5.0 * 55 * (1 - 0.10), 2)
        assert self.cart.subtotal() == expected
        # quantity 150 =>15%
        self.cart.add_item("notebook", 3.0, 150)
        expected += round(3.0 * 150 * (1 - 0.15), 2)
        assert self.cart.subtotal() == expected

    # total calculation tests
    def test_total_no_coupon_or_member(self):
        self.cart.add_item("widget", 50.0, 2)  # subtotal 100
        assert self.cart.total() == round(100 + 60, 2)

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("gadget", 200.0, 1)  # subtotal 200
        coupon_percent = parse_coupon("SAVE20")  # 20%
        discounted = round(200 * (1 - 0.20), 2)
        shipping = shipping_fee(discounted, member=True)  # half of 60 =>30
        expected_total = round(discounted + shipping, 2)
        assert self.cart.total(member=True, coupon="SAVE20") == expected_total

    def test_total_invalid_coupon(self):
        self.cart.add_item("gadget", 50.0, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

    def test_total_empty_cart_no_shipping(self):
        assert self.cart.total() == 0.00
