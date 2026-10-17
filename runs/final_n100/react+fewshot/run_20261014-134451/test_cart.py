import pytest
import cart

# ---- apply_discount -------------------------------------------------

def test_apply_discount_valid():
    # basic examples
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0

@ pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_price_negative(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_percent_out_of_range(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---- bulk_discount_percent ------------------------------------------

def test_bulk_discount_percent_cases():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("quantity", [0, -3])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---- parse_coupon -----------------------------------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save25") == 25
    assert cart.parse_coupon(" SAVE5 ") == 5

@ pytest.mark.parametrize("code", ["", "SAVEX", "SAVE0", "SAVE51", "BADCODE", "SA VE10"]) 
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---- shipping_fee -----------------------------------------------------

def test_shipping_fee():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0

@ pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Cart class ------------------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_values(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0
        assert self.cart.total() == 0

    def test_add_item_new_and_existing(self):
        self.cart.add_item("apple", 1.00, 2)
        assert self.cart.items() == {"apple": 2}
        self.cart.add_item("apple", 1.00, 3)
        assert self.cart.items() == {"apple": 5}

    def test_add_item_price_mismatch(self):
        self.cart.add_item("banana", 0.50)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 0.75)

    def test_add_item_invalid_args(self):
        with pytest.raises(ValueError):
            self.cart.add_item("orange", -1, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 1, 0)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 1, -2)

    def test_remove_item(self):
        self.cart.add_item("pear", 2.00, 3)
        self.cart.remove_item("pear")  # default quantity 1
        assert self.cart.items() == {"pear": 2}
        self.cart.remove_item("pear", 2)
        assert self.cart.items() == {}

    def test_remove_item_removes_when_zero(self):
        self.cart.add_item("peach", 3.00, 1)
        self.cart.remove_item("peach")
        assert self.cart.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("plum")

    def test_subtotal_with_bulk_discount(self):
        # 10 units at $1 each: bulk discount 5% -> line total before =10, after=9.5
        self.cart.add_item("tshirt", 1.00, 10)
        assert self.cart.subtotal() == 9.5
        # 50 units: 10% discount on line total 100 =>90
        self.cart = cart.Cart()
        self.cart.add_item("hat", 2.00, 50)
        assert self.cart.subtotal() == 90.0

    def test_total_with_coupon_and_shipping(self):
        # Setup: 20 units at $10 each => total before discount=200, bulk discount 5% ->190
        self.cart.add_item("bag", 10.00, 20)
        subtotal = self.cart.subtotal()
        assert subtotal == 190.0
        # Without coupon or member: shipping fee 60 on amount 190 =>250
        total_no_coupon = self.cart.total()
        assert total_no_coupon == round(190 + cart.shipping_fee(subtotal), 2)
        # With a valid coupon SAVE10 (10% off): discounted amount 171, shipping still based on subtotal
        total_with_coupon = self.cart.total(coupon="SAVE10")
        expected = round(171.0 + cart.shipping_fee(subtotal), 2)
        assert total_with_coupon == expected
        # Member gets half shipping: shipping fee should be 30, but code uses subtotal for fee
        member_total = self.cart.total(member=True)
        expected_member = round(subtotal + cart.shipping_fee(subtotal, member=True), 2)
        assert member_total == expected_member
