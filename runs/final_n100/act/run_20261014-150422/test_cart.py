import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- Helper constants ----------
SAMPLE_ITEM_NAME = "Widget"
UNIT_PRICE = 20.0
QUANTITY_SMALL = 5
QUANTITY_MEDIUM = 15
QUANTITY_LARGE = 55
QUANTITY_VERYLARGE = 105

# --------- apply_discount tests ---------
@pytest.mark.parametrize("price,percent,expected", [
    (200.0, 15, 170.0),
    (100, 0, 100.0),
    (50.5, 20, 40.4),
])
def test_apply_discount_valid(price, percent, expected):
    assert apply_discount(price, percent) == pytest.approx(expected)

@pytest.mark.parametrize("price,percent", [(-10, 10), (50, -5), (50, 105)])
def test_apply_discount_invalid_args(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# --------- bulk_discount_percent tests ---------
@pytest.mark.parametrize("quantity,expected", [
    (5, 0),
    (10, 5),
    (30, 5),
    (50, 10),
    (70, 10),
    (100, 15),
    (200, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [-1, 0, -5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# --------- parse_coupon tests ---------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    ("  SAVE5  ", 5),
    ("Save50", 50),
])
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVE0",
    "SAVEXX",
    "save51",
    "discount10",
    "",
    "   ",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# --------- shipping_fee tests ---------
@pytest.mark.parametrize("subtotal,member,expected", [
    (1000.0, False, 0),
    (1500, True, 0),
    (999.99, False, 60),
    (500, True, 30),
    (200, False, 60),
])
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10.0, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# --------- Cart class tests ---------
class TestCart:
    def setup_method(self):
        self.cart = Cart()

    def test_initial_state(self):
        assert self.cart.items() == []
        assert self.cart.subtotal() == 0
        assert self.cart.total() == 0

    def test_add_item_single_unit(self):
        self.cart.add_item(SAMPLE_ITEM_NAME, UNIT_PRICE)
        assert len(self.cart.items()) == 1
        item = self.cart.items()[0]
        assert item["name"] == SAMPLE_ITEM_NAME
        assert item["unit_price"] == UNIT_PRICE
        assert item["quantity"] == 1
        assert self.cart.subtotal() == pytest.approx(UNIT_PRICE)

    def test_add_item_multiple_units(self):
        self.cart.add_item(SAMPLE_ITEM_NAME, UNIT_PRICE, QUANTITY_MEDIUM)
        item = self.cart.items()[0]
        assert item["quantity"] == QUANTITY_MEDIUM
        expected_subtotal = UNIT_PRICE * QUANTITY_MEDIUM
        assert self.cart.subtotal() == pytest.approx(expected_subtotal)

    def test_add_multiple_different_items(self):
        self.cart.add_item("Gadget", 10.0, 3)
        self.cart.add_item(SAMPLE_ITEM_NAME, UNIT_PRICE, QUANTITY_SMALL)
        assert len(self.cart.items()) == 2
        names = {i["name"] for i in self.cart.items()}
        assert names == {"Gadget", SAMPLE_ITEM_NAME}
        expected_subtotal = 10.0 * 3 + UNIT_PRICE * QUANTITY_SMALL
        assert self.cart.subtotal() == pytest.approx(expected_subtotal)

    def test_remove_item(self):
        self.cart.add_item(SAMPLE_ITEM_NAME, UNIT_PRICE, QUANTITY_LARGE)
        self.cart.remove_item(SAMPLE_ITEM_NAME, 30)
        item = next((i for i in self.cart.items() if i["name"] == SAMPLE_ITEM_NAME), None)
        assert item is not None
        assert item["quantity"] == QUANTITY_LARGE - 30
        self.cart.remove_item(SAMPLE_ITEM_NAME, QUANTITY_LARGE - 30)
        assert len(self.cart.items()) == 0

    def test_total_with_member_and_coupon(self):
        self.cart.add_item("Expensive", 1200.0, 1)
        total = self.cart.total(member=True, coupon="SAVE20")
        expected_subtotal = 1200.0
        discounted = apply_discount(expected_subtotal, 20)
        assert total == pytest.approx(discounted)

    def test_total_no_coupon(self):
        self.cart.add_item(SAMPLE_ITEM_NAME, UNIT_PRICE, QUANTITY_SMALL)
        expected = UNIT_PRICE * QUANTITY_SMALL + 60
        assert self.cart.total() == pytest.approx(expected)

    def test_total_with_invalid_coupon(self):
        self.cart.add_item(SAMPLE_ITEM_NAME, UNIT_PRICE, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")
