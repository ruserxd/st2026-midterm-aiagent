import pytest
import cart

# ----- apply_discount -------------------------------------------------

def test_apply_discount_normal():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100.00, 0) == 100.0
    assert cart.apply_discount(50.55, 10) == round(50.55 * 0.9, 2)

@ pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_price_negative(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_percent_invalid(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ----- bulk_discount_percent ------------------------------------------

def test_bulk_discount_percent_bounds():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

@ pytest.mark.parametrize("quantity", [0, -3])
def test_bulk_discount_negative_or_zero(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ----- parse_coupon ---------------------------------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon(" save20 ") == 20
    assert cart.parse_coupon("SaVe1") == 1
    assert cart.parse_coupon("sAvE50") == 50

@ pytest.mark.parametrize("code", ["save0", "SAVE51", "INVALID", "SAVExx", "123"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ----- shipping_fee ---------------------------------------------------

def test_shipping_fee_non_member():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0

@ pytest.mark.parametrize("subtotal", [0, 499])
def test_shipping_fee_member(subtotal):
    assert cart.shipping_fee(subtotal, member=True) == 30

@ pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ----- Cart class -----------------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_items(self):
        self.cart.add_item("apple", 1.0, quantity=3)
        self.cart.add_item("banana", 0.5)
        assert self.cart.items() == {"apple": 3, "banana": 1}

    def test_add_existing_increases_quantity_and_requires_same_price(self):
        self.cart.add_item("apple", 1.0, quantity=2)
        self.cart.add_item("apple", 1.0, quantity=4)
        assert self.cart.items()["apple"] == 6
        with pytest.raises(ValueError):
            self.cart.add_item("apple", 2.0, quantity=1)

    def test_remove(self):
        self.cart.add_item("pear", 0.75, quantity=5)
        self.cart.remove_item("pear", quantity=3)
        assert self.cart.items()["pear"] == 2
        # remove the rest should drop the item
        self.cart.remove_item("pear", quantity=2)
        assert "pear" not in self.cart.items()

    def test_remove_not_in_cart_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("notthere")

    def test_subtotal_no_bulk_discount(self):
        # 2 apples at $1 each, no bulk discount
        self.cart.add_item("apple", 1.0, quantity=2)
        assert self.cart.subtotal() == 2.0

    def test_subtotal_with_bulk_discount(self):
        # 10 oranges at $2 each, bulk discount 5%
        self.cart.add_item("orange", 2.0, quantity=10)
        expected = round(2.0 * 10 * (1 - 0.05), 2)
        assert self.cart.subtotal() == expected

    def test_total_no_coupon_or_shipping(self):
        # subtotal < 1000 so shipping applies; no member, no coupon
        self.cart.add_item("item", 20.0, quantity=5)  # subtotal = 100
        total_expected = round(100 + cart.shipping_fee(100), 2)
        assert self.cart.total() == total_expected

    def test_total_with_coupon_and_member(self):
        # subtotal = 200 (bulk discount applied on items)
        self.cart.add_item("item", 20.0, quantity=10)  # bulk discount for 10 units
        subtotal = self.cart.subtotal()
        after_coupon = round(subtotal * (1 - cart.parse_coupon("SAVE10") / 100), 2)
        shipping = cart.shipping_fee(after_coupon, member=True)
        total_expected = round(after_coupon + shipping, 2)
        assert self.cart.total(member=True, coupon="SAVE10") == total_expected

    def test_total_empty_cart(self):
        assert self.cart.total() == 0.0

    def test_total_invalid_coupon_raises(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

    def test_subtotal_rounding(self):
        # create a scenario where rounding matters
        self.cart.add_item("pencil", 0.333, quantity=3)  # 0.999 without discount
        assert self.cart.subtotal() == round(0.999, 2)
