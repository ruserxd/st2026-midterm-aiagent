import pytest
import cart

# ---------- apply_discount ---------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize(
    "price, percent, expected",
    [ (100, 0, 100.0),
      (123.45, 10, 111.11),  # 123.45 * 0.9 = 111.105 -> rounded to 111.11
      (50, 100, 0.0) ]
)
def test_apply_discount_various(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# Invalid inputs
@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 150])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent ---------

def test_bulk_discount_percent_boundaries():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

with pytest.raises(ValueError):
    cart.bulk_discount_percent(-1)

# ---------- parse_coupon ---------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon(" save25 ") == 25
    assert cart.parse_coupon("SaVe50") == 50

@pytest.mark.parametrize(
    "code",
    ["", "SAVE0", "SAVE51", "DISCOUNT10", "SAVEX"]
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ---------

def test_shipping_fee_non_member():
    assert cart.shipping_fee(999) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(2000) == 0

def test_shipping_fee_member():
    assert cart.shipping_fee(999, member=True) == 30
    assert cart.shipping_fee(1000, member=True) == 0

with pytest.raises(ValueError):
    cart.shipping_fee(-10)

# ---------- Cart ---------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_item_new(self):
        self.cart.add_item("apple", 2.0, 3)
        assert self.cart.items() == {"apple": 3}

    def test_add_item_increment(self):
        self.cart.add_item("banana", 1.5, 2)
        self.cart.add_item("banana", 1.5, 3)
        assert self.cart.items() == {"banana": 5}

    def test_add_item_price_mismatch(self):
        self.cart.add_item("cherry", 0.5, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("cherry", 0.6, 2)

    @pytest.mark.parametrize("unit_price", [-1, -0.01])
    def test_add_item_negative_price(self, unit_price):
        with pytest.raises(ValueError):
            self.cart.add_item("durian", unit_price, 1)

    @pytest.mark.parametrize("quantity", [0, -5, 2.5])
    def test_add_item_invalid_quantity(self, quantity):
        with pytest.raises(ValueError):
            self.cart.add_item("eggplant", 3.0, quantity)

    def test_remove_item_partial_and_complete(self):
        self.cart.add_item("fig", 2.0, 4)
        self.cart.remove_item("fig", 1)
        assert self.cart.items() == {"fig": 3}
        self.cart.remove_item("fig", 3)
        assert self.cart.items() == {}

    def test_remove_item_not_present(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("grape", 1)

    def test_subtotal_with_bulk_discount(self):
        # 10 units of milk at $5 each => bulk discount 5%
        self.cart.add_item("milk", 5.0, 10)
        expected = round(5.0 * 10 * (1 - 0.05), 2)  # 47.5
        assert self.cart.subtotal() == expected

    def test_subtotal_multiple_items(self):
        self.cart.add_item("bread", 3.0, 9)   # no discount
        self.cart.add_item("butter", 2.0, 50)  # 10% discount
        subtotal = (3.0 * 9) + (2.0 * 50 * 0.90)
        assert self.cart.subtotal() == round(subtotal, 2)

    def test_total_no_coupon_member(self):
        self.cart.add_item("candy", 1.0, 20)  # 5% discount => 19.0
        subtotal = 1.0 * 20 * 0.95
        total_expected = round(subtotal + cart.shipping_fee(subtotal, member=True), 2)
        assert self.cart.total(member=True) == total_expected

    def test_total_with_coupon(self):
        self.cart.add_item("juice", 4.0, 5)  # no bulk discount => 20.0
        # coupon SAVE10 gives 10% off subtotal
        subtotal = 20.0
        discounted = round(subtotal * (1 - 0.10), 2)
        total_expected = round(discounted + cart.shipping_fee(discounted, member=False), 2)
        assert self.cart.total(coupon="SAVE10") == total_expected

    def test_total_invalid_coupon(self):
        self.cart.add_item("kale", 3.0, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")

    def test_total_empty_cart(self):
        assert self.cart.total() == 0
        assert self.cart.total(member=True) == 0
        assert self.cart.total(coupon="SAVE10") == 0
