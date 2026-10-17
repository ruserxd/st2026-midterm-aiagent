import pytest
import cart

# --- apply_discount -----------------------------------------------------------

def test_apply_discount_normal():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0

@ pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [-1, 101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# --- bulk_discount_percent -----------------------------------------------------

def test_bulk_discount_percent():
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

# --- parse_coupon --------------------------------------------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save25 ") == 25
    assert cart.parse_coupon("  SaVe1") == 1
    assert cart.parse_coupon(" SAVE50 ") == 50

@ pytest.mark.parametrize("code", ["",
                                     "ABC10",
                                     "SAVE0",
                                     "SAVE51",
                                     "SAVEXX"]) 
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee --------------------------------------------------------------

def test_shipping_fee_free_and_member():
    assert cart.shipping_fee(999) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(1000, member=True) == 0

@ pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --- Cart class tests ----------------------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initially_empty(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    # add_item tests
    def test_add_single_item(self):
        self.cart.add_item("apple", 1.0, 2)
        assert self.cart.items() == {"apple": 2}
        assert self.cart.subtotal() == 2.0

    def test_add_existing_same_price_increases_qty(self):
        self.cart.add_item("banana", 0.5, 3)
        self.cart.add_item("banana", 0.5, 2)
        assert self.cart.items() == {"banana": 5}
        assert self.cart.subtotal() == 2.5

    def test_add_existing_different_price_raises(self):
        self.cart.add_item("orange", 0.8)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 1.0)

    @ pytest.mark.parametrize("unit_price, qty", [( -1, 1), (1.0, 0), (1.0, -3)])
    def test_add_invalid_args(self, unit_price, qty):
        with pytest.raises(ValueError):
            self.cart.add_item("test", unit_price, qty)

    # remove_item tests
    def test_remove_partial_quantity(self):
        self.cart.add_item("mango", 2.0, 5)
        self.cart.remove_item("mango", 3)
        assert self.cart.items() == {"mango": 2}

    def test_remove_entire_and_more(self):
        self.cart.add_item("pear", 1.5, 4)
        self.cart.remove_item("pear", 4)  # should remove item
        assert "pear" not in self.cart.items()
        self.cart.remove_item("pear", 1)  # removing non-existent should raise KeyError
        with pytest.raises(KeyError):
            self.cart.remove_item("pear", 1)

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent", 1)

    # subtotal with bulk discount
    def test_subtotal_bulk_discount(self):
        self.cart.add_item("pen", 1.0, 9)   # no discount
        assert self.cart.subtotal() == 9.0
        self.cart.remove_item("pen", 0)
        self.cart.add_item("pen", 1.0, 10)  # 5% discount on each of the 10 pens
        assert self.cart.subtotal() == round(10 * 1.0 * (1 - 0.05), 2)
        self.cart.remove_item("pen", 50)   # invalid quantity removal? zero qty leads to no change

    def test_total_with_coupon_and_shipping(self):
        self.cart.add_item("giftcard", 100.0, 1)
        total = self.cart.total(coupon="SAVE20")
        expected_after_coupon = round(100.0 * (1 - 0.20), 2)
        shipping = cart.shipping_fee(expected_after_coupon)
        assert total == round(expected_after_coupon + shipping, 2)

    def test_total_member_shipping(self):
        self.cart.add_item("tshirt", 50.0, 3)  # subtotal 150, no bulk discount
        total = self.cart.total(member=True)
        expected_subtotal = 150.0
        shipping = cart.shipping_fee(expected_subtotal, member=True)
        assert total == round(expected_subtotal + shipping, 2)

    def test_total_empty_cart_no_shipping(self):
        assert self.cart.total() == 0.0
