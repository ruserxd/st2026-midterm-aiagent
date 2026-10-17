import pytest
import cart

# ---------- helpers for expected values ----------

def exp_apply_discount(price, percent):
    return round(price * (1 - percent / 100), 2)

# ---------- apply_discount tests ----------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (10, 0, 10.00),
    (10, 100, 0.0),
])
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [
    (-1, 20),   # negative price
    (10, -5),   # negative percent
    (10, 105),  # percent >100
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent tests ----------
@pytest.mark.parametrize("qty,expected", [
    (5, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -5, 3.7])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- parse_coupon tests ----------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVE0",
    "SAVEXX",
    "DISCOUNT5",
    "save-10",
    "   ",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee tests ----------
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (999.99, False, 60),
    (1000, False, 0),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart tests ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_values(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.00
        assert self.cart.total() == 0.00

    def test_add_item_new_and_existing(self):
        self.cart.add_item("Apple", 1.5, 2)
        assert self.cart.items() == {"Apple": 2}
        # same item with same price increases quantity
        self.cart.add_item("Apple", 1.5, 3)
        assert self.cart.items() == {"Apple": 5}
        # adding another product
        self.cart.add_item("Banana", 0.75)
        assert self.cart.items() == {"Apple": 5, "Banana": 1}

    def test_add_item_invalid(self):
        with pytest.raises(ValueError):
            self.cart.add_item("Pear", -1.0)
        with pytest.raises(ValueError):
            self.cart.add_item("Pear", 1.0, 0)
        with pytest.raises(ValueError):
            self.cart.add_item("Pear", 1.0, 2.5)

    def test_add_item_price_mismatch(self):
        self.cart.add_item("Mango", 3.0, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("Mango", 4.0, 1)

    def test_remove_item_basic_and_zero_removal(self):
        self.cart.add_item("Orange", 2.0, 3)
        self.cart.remove_item("Orange", 1)
        assert self.cart.items() == {"Orange": 2}
        # removing remaining quantity removes the key
        self.cart.remove_item("Orange", 2)
        assert "Orange" not in self.cart.items()

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("Grape", 1)

    def test_subtotal_with_bulk_discount(self):
        # 12 units => bulk discount 5%
        self.cart.add_item("Notebook", 10.0, 12)
        expected = round(12 * 10.0 * (1 - 5/100), 2)  # 114.0
        assert self.cart.subtotal() == expected

    def test_total_with_coupon_and_shipping(self):
        # items: 3 of ItemA at $20 each -> bulk discount none
        self.cart.add_item("ItemA", 20, 3)
        subtotal = 60.0
        # apply coupon SAVE10 => 6 off
        total_before_ship = round(subtotal * (1 - 10/100), 2)  # 54.0
        shipping = cart.shipping_fee(total_before_ship, member=False)
        expected_total = round(total_before_ship + shipping, 2)
        assert self.cart.total(coupon="SAVE10") == expected_total

    def test_total_membership_and_no_shipping(self):
        # big purchase to get free shipping
        self.cart.add_item("Widget", 500, 3)  # subtotal 1500
        # no coupon
        total = self.cart.total(member=True)
        assert total == round(1500.0 + cart.shipping_fee(1500.0, True), 2)

    def test_total_empty_no_shipping(self):
        assert self.cart.total() == 0.00
