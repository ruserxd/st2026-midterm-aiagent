import pytest
import cart

# Helper for rounding as per spec

def round2(x):
    return round(x, 2)

# ----- apply_discount -----
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (100, 100, 0.0),
])
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [(-1, 10), (50, -5), (50, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ----- bulk_discount_percent -----
@pytest.mark.parametrize("quantity,result", [
    (5, 0), (9, 0), (10, 5), (49, 5), (50, 10), (99, 10), (100, 15), (150, 15)
])
def test_bulk_discount_percent(quantity, result):
    assert cart.bulk_discount_percent(quantity) == result

@pytest.mark.parametrize("quantity", [0, -1, 3.5, "ten"])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ----- parse_coupon -----
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    ("save20", 20),
    ("  SaVe5  ", 5),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "SAVEX10", "foo", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ----- shipping_fee -----
@pytest.mark.parametrize("subtotal,member,fee", [
    (999.99, False, 60),
    (1000, False, 0),
    (1200, True, 30),
])
def test_shipping_fee(subtotal, member, fee):
    assert cart.shipping_fee(subtotal, member) == fee

@pytest.mark.parametrize("subtotal", [-10, -1.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ----- Cart class -----
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_item_new(self):
        self.cart.add_item("apple", 1.5, 2)
        assert self.cart.items() == {"apple": 2}

    def test_add_item_increase_quantity_same_price(self):
        self.cart.add_item("banana", 0.5, 3)
        self.cart.add_item("banana", 0.5, 2)
        assert self.cart.items() == {"banana": 5}

    def test_add_item_different_price_error(self):
        self.cart.add_item("orange", 1.0, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 1.2, 1)

    def test_add_item_invalid_params(self):
        with pytest.raises(ValueError):
            self.cart.add_item("pear", -1, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 0.5, 0)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 0.5, "two")

    def test_remove_item_basic(self):
        self.cart.add_item("milk", 2.0, 3)
        self.cart.remove_item("milk", 1)
        assert self.cart.items() == {"milk": 2}

    def test_remove_item_to_zero_removes(self):
        self.cart.add_item("juice", 3.0, 2)
        self.cart.remove_item("juice", 2)
        assert self.cart.items() == {}

    def test_remove_item_more_than_present(self):
        self.cart.add_item("tea", 1.5, 1)
        self.cart.remove_item("tea", 5)
        assert self.cart.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("coffee", 1)

    def test_subtotal_no_items(self):
        assert round2(self.cart.subtotal()) == 0.0

    def test_subtotal_with_bulk_discount(self):
        # 10 apples at $1 each => bulk discount 5% => subtotal = 10 * 1 * 0.95
        self.cart.add_item("apple", 1.0, 10)
        assert round2(self.cart.subtotal()) == round2(10 * 1.0 * 0.95)

    def test_total_without_coupon_or_member(self):
        self.cart.add_item("bread", 5.0, 1)  # subtotal 5.0
        # shipping fee: subtotal <1000 => 60
        assert round2(self.cart.total()) == round2(5.0 + 60)

    def test_total_with_coupon(self):
        self.cart.add_item("bagel", 4.0, 1)
        # subtotal 4.0, coupon SAVE10 -> discount 10% => 3.6
        assert round2(self.cart.total(coupon="SAVE10")) == round2(3.6 + cart.shipping_fee(3.6))

    def test_total_member_shipping_half(self):
        self.cart.add_item("toy", 20.0, 1)
        # subtotal 20 -> shipping 60 for non-member, 30 for member
        assert round2(self.cart.total(member=True)) == round2(20 + cart.shipping_fee(20, member=True))

    def test_total_empty_cart_zero(self):
        assert round2(self.cart.total()) == 0.0

    def test_total_invalid_coupon_raises(self):
        self.cart.add_item("item", 1.0, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")
