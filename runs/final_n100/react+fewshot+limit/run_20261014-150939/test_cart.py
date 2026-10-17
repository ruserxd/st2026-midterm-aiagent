import pytest
import cart

# --- apply_discount -------------------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price,percent,result", [
    (100, 0, 100.0),        # no discount
    (100, 100, 0.0),        # full discount
])
def test_apply_discount_bounds(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# error cases for apply_discount
@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_price_negative(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_percent_out_of_range(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# --- bulk_discount_percent -----------------------------------

def test_bulk_discount_percent_values():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

@pytest.mark.parametrize("qty", [0, -1])
def test_bulk_discount_percent_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# --- parse_coupon --------------------------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save25 ") == 25
    assert cart.parse_coupon("   SaVe1") == 1
    assert cart.parse_coupon("sAvE50") == 50

@pytest.mark.parametrize("code", ["", "SAVEBAD", "SAVE0", "SAVE51", "12310", "SAVE-5"]) 
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee --------------------------------------------

def test_shipping_fee_non_member():
    assert cart.shipping_fee(500) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(999.99) == 60

def test_shipping_fee_member():
    assert cart.shipping_fee(200, member=True) == 30
    assert cart.shipping_fee(1000, member=True) == 0

@pytest.mark.parametrize("subtotal", [-10, -0.01])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --- Cart class -----------------------------------------------

class TestCartBasics:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initial_empty(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    def test_add_item_new(self):
        self.cart.add_item("apple", 2.5, 3)
        assert self.cart.items() == {"apple": 3}
        # subtotal should account for bulk discount: qty=3 <10 -> no discount
        assert self.cart.subtotal() == 7.5

    def test_add_existing_same_price(self):
        self.cart.add_item("banana", 1.0, 2)
        self.cart.add_item("banana", 1.0, 4)
        assert self.cart.items() == {"banana": 6}
        # qty=6 => bulk_discount_percent =5% -> discount
        expected = round(1.0 * 6 * (1 - 0.05), 2)  # 5.70
        assert self.cart.subtotal() == expected

    def test_add_existing_different_price_raises(self):
        self.cart.add_item("pear", 3.0, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 4.0, 2)

    def test_remove_partial(self):
        self.cart.add_item("orange", 1.5, 5)
        self.cart.remove_item("orange", 2)
        assert self.cart.items() == {"orange": 3}
        # subtotal qty=3 -> no bulk discount
        assert self.cart.subtotal() == 4.5

    def test_remove_all(self):
        self.cart.add_item("grape", 0.8, 2)
        self.cart.remove_item("grape", 2)
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0

    def test_remove_more_than_exists(self):
        self.cart.add_item("melon", 3.5, 1)
        # removing more than present should remove item
        self.cart.remove_item("melon", 5)
        assert self.cart.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent", 1)

    def test_total_with_coupon_and_shipping(self):
        # subtotal before discount: 3 items of $10 => qty=3, no bulk
        self.cart.add_item("widget", 10.0, 3)
        # coupon SAVE20 -> 20%
        total = self.cart.total(member=False, coupon="SAVE20")
        # after coupon: 30 * 0.8 = 24.0; shipping fee 60 -> 84.0
        assert total == 84.0

    def test_total_no_shipping_when_free(self):
        self.cart.add_item("expensive", 400.0, 3)  # subtotal 1200
        total = self.cart.total(member=False)
        # shipping free, no discount -> 1200
        assert total == 1200.0

    def test_total_empty_cart(self):
        assert self.cart.total() == 0.0

# End of tests
