import pytest
import cart

# ---- apply_discount -----------------------------------------------------

def test_apply_discount_valid_cases():
    assert cart.apply_discount(200, 15) == 170.0
    # percent on edge cases
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0

# Out of range inputs should raise ValueError
@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 20)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---- bulk_discount_percent -----------------------------------------------

def test_bulk_discount_percent_cases():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@pytest.mark.parametrize("quantity", [0, -1])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---- parse_coupon -------------------------------------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon("  SaVe5 ") == 5

@pytest.mark.parametrize("code", ["SAVEX", "SAVE0", "SAVE51", "WRONG", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---- shipping_fee --------------------------------------------------------

def test_shipping_fee_non_member():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(0) == 60

def test_shipping_fee_member():
    assert cart.shipping_fee(200, member=True) == 30
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(1000, member=True) == 0

@pytest.mark.parametrize("subtotal", [-1])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Cart class ----------------------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_items(self):
        self.cart.add_item("apple", 1.0, 3)
        self.cart.add_item("banana", 2.0)
        assert self.cart.items() == {"apple": 3, "banana": 1}

    def test_add_existing_increase_quantity(self):
        self.cart.add_item("apple", 1.5, 2)
        self.cart.add_item("APPLE", 1.5, 3)  # case-sensitive name
        assert self.cart.items() == {"apple": 2, "APPLE": 3}

    def test_add_inconsistent_unit_price(self):
        self.cart.add_item("orange", 1.0)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 1.5)

    def test_remove_item(self):
        self.cart.add_item("pear", 2.5, 4)
        self.cart.remove_item("pear", 2)
        assert self.cart.items() == {"pear": 2}
        # removing enough to zero removes entry
        self.cart.remove_item("pear", 2)
        assert self.cart.items() == {}

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent")

    def test_subtotal_bulk_discount(self):
        # 20 apples at $1 each: bulk discount 5% -\u003e 0.05 * 20 = $1 off
        self.cart.add_item("apple", 1.0, 20)
        assert self.cart.subtotal() == 19.0

    def test_total_no_items(self):
        assert self.cart.total() == 0

    def test_total_with_coupon_and_shipping(self):
        # Add 3 units of an item costing $10 each -\u003e no bulk discount
        self.cart.add_item("widget", 10.0, 3)
        # subtotal = 30
        total = self.cart.total(coupon="SAVE10")
        # coupon reduces by 10% -> 27, shipping fee (non-member) is 60
        # final = 87
        assert total == 87.0

    def test_total_member_no_shipping(self):
        self.cart.add_item("bigitem", 200.0, 5)
        # no bulk discount; subtotal=1000 -\u003e shipping free
        assert self.cart.total(member=True) == 1000.0

    def test_total_invalid_coupon(self):
        self.cart.add_item("foo", 10.0)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BAD")
