import pytest
import cart

# --- apply_discount -------------------------------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize("price,percent,expected", [
    (100, 0, 100.0),
    (100, 100, 0.0),
])
def test_apply_discount_edges(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@ pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 20)

@ pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# --- bulk_discount_percent -----------------------------------------------

def test_bulk_discount_percent_basic():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("quantity", [0, -5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --- parse_coupon ----------------------------------------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon(" save25 ") == 25
    assert cart.parse_coupon("sAvE50") == 50

@ pytest.mark.parametrize("code", ["SAVEXX", "SA5", "DISCOUNT", "save51", "", "   "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee ----------------------------------------------------------

def test_shipping_fee_free_and_half():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1200) == 0
    # member half fee
    for subtotal in [10, 500, 999]:
        assert cart.shipping_fee(subtotal, member=True) == 30

@ pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --- Cart class ------------------------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_items_empty(self):
        assert self.cart.items() == {}

    def test_add_single_item(self):
        self.cart.add_item("apple", 1.0, 3)
        assert self.cart.items() == {"apple": 3}

    def test_add_same_item_increments(self):
        self.cart.add_item("banana", 2.5)
        self.cart.add_item("banana", 2.5, 2)
        assert self.cart.items() == {"banana": 3}

    def test_add_different_price_raises(self):
        self.cart.add_item("orange", 1.0)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 1.5)

    def test_remove_item_decrease_and_removal(self):
        self.cart.add_item("pear", 3.0, 4)
        self.cart.remove_item("pear", 2)
        assert self.cart.items() == {"pear": 2}
        self.cart.remove_item("pear", 2)
        assert self.cart.items() == {}

    def test_remove_not_in_cart_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("mango")

    def test_subtotal_no_bulk_discount(self):
        self.cart.add_item("pen", 2.0, 5)  # qty <10 => no bulk discount
        assert self.cart.subtotal() == 10.0

    def test_subtotal_with_bulk_discount(self):
        self.cart.add_item("pencil", 1.0, 12)  # qty >=10 => 5% off
        expected = round(1.0 * 12 * 0.95, 2)
        assert self.cart.subtotal() == expected

    def test_subtotal_rounding(self):
        self.cart.add_item("item", 1.3333, 10)  # bulk discount applies
        expected = round(1.3333 * 10 * 0.95, 2)
        assert self.cart.subtotal() == expected

    def test_total_no_coupon_or_shipping(self):
        self.cart.add_item("widget", 200.0, 4)  # no bulk discount
        # subtotal = 800; shipping fee 60
        assert self.cart.total() == 860.0

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("gadget", 300.0, 2)
        subtotal = 600.0
        discount_percent = cart.parse_coupon("SAVE20")  # 20%
        discounted = cart.apply_discount(subtotal, discount_percent)
        shipping_fee = cart.shipping_fee(discounted, member=True)
        expected_total = round(discounted + shipping_fee, 2)
        assert self.cart.total(member=True, coupon="SAVE20") == expected_total

    def test_total_empty_cart(self):
        assert self.cart.total() == 0

    def test_total_invalid_coupon_raises(self):
        self.cart.add_item("test", 10.0)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")
