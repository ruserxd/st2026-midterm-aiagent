import pytest
import cart

# ---- apply_discount -------------------------------------------------

def test_apply_discount_valid():
    assert cart.apply_discount(200, 15) == 170.0
    # rounding to two decimals
    assert cart.apply_discount(100, 33) == 67.0

@pytest.mark.parametrize("price,percent", [(-1,10),(50,-5),(50,101)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---- bulk_discount_percent -------------------------------------------

def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@pytest.mark.parametrize("qty", [0,-3,1.5])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---- parse_coupon -----------------------------------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save5") == 5
    assert cart.parse_coupon(" SAVE25 ") == 25

@pytest.mark.parametrize("code", ["SAV10","SAVE0","SAVE51","NOTVALID","SAVE-1"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---- shipping_fee -----------------------------------------------------

def test_shipping_fee():
    # subtotal >= 1000 -> free
    assert cart.shipping_fee(1000) == 0.0
    assert cart.shipping_fee(1500) == 0.0
    # otherwise fee 60, members half
    assert cart.shipping_fee(999) == 60.0
    assert cart.shipping_fee(500, member=True) == 30.0

@pytest.mark.parametrize("subtotal", [-1,-10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Cart functionality -----------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_items(self):
        self.cart.add_item("apple", 1.0, 3)
        self.cart.add_item("banana", 0.5, 2)
        assert self.cart.items() == {"apple": 3, "banana": 2}

    def test_add_existing_updates_quantity_and_price_check(self):
        self.cart.add_item("apple", 1.0, 3)
        # same unit price, increases quantity
        self.cart.add_item("apple", 1.0, 2)
        assert self.cart.items() == {"apple": 5}
        # different price raises ValueError
        with pytest.raises(ValueError):
            self.cart.add_item("apple", 1.5, 1)

    def test_remove_item(self):
        self.cart.add_item("apple", 2.0, 3)
        self.cart.remove_item("apple", 1)
        assert self.cart.items() == {"apple": 2}
        # remove more than existing -> item removed
        self.cart.remove_item("apple", 5)
        assert self.cart.items() == {}

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("pear", 1)

    def test_subtotal_no_bulk_discount(self):
        self.cart.add_item("apple", 2.0, 3)   # qty<10 -> no bulk discount
        assert self.cart.subtotal() == 6.00

    def test_subtotal_with_bulk_discount(self):
        self.cart.add_item("apple", 2.0, 12)  # qty>=10 -> 5% discount
        expected = round(2.0*12 * (1-0.05), 2)
        assert self.cart.subtotal() == expected

    def test_total_no_coupon_or_member(self):
        self.cart.add_item("item", 100.0, 1)
        # subtotal 100, no shipping (subtotal<1000)
        # shipping fee 60 added => total 160
        assert self.cart.total() == 160.00

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("item", 200.0, 5)   # subtotal 1000, bulk discount 10% -> 900
        # coupon SAVE10 => 90
        # shipping fee on 90: member True -> half of 60 = 30
        assert self.cart.total(member=True, coupon="SAVE10") == 120.00

    def test_total_empty_cart(self):
        assert self.cart.total() == 0.0
