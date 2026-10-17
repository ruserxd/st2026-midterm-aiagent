import pytest
import cart

# --------------------------- apply_discount ---------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price,percent", [(-10, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --------------------------- bulk_discount_percent --------------------------

def test_bulk_discount_percent_levels():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(100) == 15

@pytest.mark.parametrize("quantity", [0, -1, 2.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --------------------------- parse_coupon -----------------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon(" save20 ") == 20
    assert cart.parse_coupon("SaVe50") == 50

@pytest.mark.parametrize("code", ["", "SAVEX", "SAVE0", "SAVE51", "abc123"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --------------------------- shipping_fee -----------------------------------

def test_shipping_fee_basic():
    assert cart.shipping_fee(999) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(500, member=True) == 30

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --------------------------- Cart class -------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0
        assert self.cart.total() == 0

    def test_add_item_new_and_increase(self):
        self.cart.add_item("apple", 100, 2)
        assert self.cart.items() == {"apple": 2}
        # adding same item with same price increases quantity
        self.cart.add_item("apple", 100, 3)
        assert self.cart.items() == {"apple": 5}

    def test_add_item_invalid(self):
        with pytest.raises(ValueError):
            self.cart.add_item("orange", -5, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 5, 0)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 5, 2.3)

    def test_add_item_price_mismatch(self):
        self.cart.add_item("banana", 50, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 60, 1)

    def test_remove_item_partial_and_full(self):
        self.cart.add_item("mango", 200, 4)
        # remove fewer than quantity
        self.cart.remove_item("mango", 2)
        assert self.cart.items() == {"mango": 2}
        # remove remaining quantity
        self.cart.remove_item("mango", 2)
        assert "mango" not in self.cart.items()

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("pear", 1)

    def test_subtotal_with_bulk_discount(self):
        # quantity 10 -> 5% discount, quantity 50 -> 10%, quantity 100->15%
        self.cart.add_item("itemA", 100, 10)   # 1000 - 5% = 950
        self.cart.add_item("itemB", 200, 50)   # 10000 -10% = 9000
        expected = round(950 + 9000, 2)
        assert self.cart.subtotal() == expected

    def test_total_no_coupon_non_member(self):
        self.cart.add_item("item", 500, 1)  # subtotal 500
        total = self.cart.total()
        # subtotal 500 + shipping 60 = 560
        assert total == round(500 + 60, 2)

    def test_total_with_coupon_member(self):
        self.cart.add_item("item", 2000, 1)  # subtotal 2000
        total = self.cart.total(member=True, coupon="SAVE10")
        # after coupon: 1800, shipping free
        assert total == round(1800 + 0, 2)

    def test_total_invalid_coupon(self):
        self.cart.add_item("item", 100, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")

    def test_total_empty_cart_no_shipping(self):
        assert self.cart.total() == 0
        # even if member or coupon supplied
        assert self.cart.total(member=True, coupon="SAVE10") == 0
