import pytest
import cart

# ---------- apply_discount tests ----------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price,percent,result", [
    (100, 0, 100.0),           # no discount
    (100, 100, 0.0),          # full discount
])
def test_apply_discount_various(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# boundary values for percent and price
@pytest.mark.parametrize("price,percent", [(-1, 10), (50, -5), (50, 105)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent tests ----------

def test_bulk_discount_basic():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

@pytest.mark.parametrize("quantity", [0, -5, 3.7])
def test_bulk_discount_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon tests ----------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save5 ") == 5
    assert cart.parse_coupon("   SaVe50  ") == 50

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "abc", "SAVE-1", "SAVEXX"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee tests ----------

def test_shipping_fee_basic():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0

# member half fee
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(1100, member=True) == 0

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class tests ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initial_state(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    # add_item tests
    def test_add_new_item(self):
        self.cart.add_item("apple", 1.00, 3)
        assert self.cart.items() == {"apple": 3}

    def test_add_existing_same_price(self):
        self.cart.add_item("banana", 0.50, 2)
        self.cart.add_item("banana", 0.50, 4)
        assert self.cart.items() == {"banana": 6}

    def test_add_existing_different_price_error(self):
        self.cart.add_item("orange", 1.20, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 1.30, 2)

    @pytest.mark.parametrize("quantity", [0, -3])
    def test_add_invalid_quantity(self, quantity):
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 0.80, quantity)

    @pytest.mark.parametrize("unit_price", [-1, "a"] )
    def test_add_invalid_unit_price(self, unit_price):
        with pytest.raises(ValueError):
            self.cart.add_item("kiwi", unit_price, 2)

    # remove_item tests
    def test_remove_some_quantity(self):
        self.cart.add_item("mango", 2.00, 5)
        self.cart.remove_item("mango", 3)
        assert self.cart.items() == {"mango": 2}

    def test_remove_entirely(self):
        self.cart.add_item("peach", 1.50, 4)
        self.cart.remove_item("peach", 4)
        assert "peach" not in self.cart.items()

    def test_remove_more_than_exists_removes(self):
        self.cart.add_item("plum", 0.70, 2)
        self.cart.remove_item("plum", 5)  # should remove entirely
        assert "plum" not in self.cart.items()

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonitem", 1)

    # subtotal calculations
    def test_subtotal_no_discount(self):
        self.cart.add_item("x", 10.0, 9)   # quantity <10 -> no discount
        assert self.cart.subtotal() == 90.0

    def test_subtotal_with_bulk_discount(self):
        self.cart.add_item("y", 5.0, 12)  # quantity 12 -> 5% discount
        expected = round(5.0*12*(1-0.05),2)
        assert self.cart.subtotal() == expected

    def test_subtotal_multiple_items(self):
        self.cart.add_item("a", 3.0, 10)   # 5% off -> 28.5
        self.cart.add_item("b", 4.0, 51)   # 10% off -> 19.32
        total = round(28.5 + 19.32,2)
        assert self.cart.subtotal() == total

    # total with coupon and shipping
    def test_total_no_coupon(self):
        self.cart.add_item("c", 200.0, 1)   # subtotal 200
        # shipping 60 (subtotal<1000, non-member)
        assert self.cart.total() == round(200+60,2)

    def test_total_with_valid_coupon(self):
        self.cart.add_item("d", 300.0, 1)   # subtotal 300
        # coupon SAVE10 -> 10% off => 270
        # shipping on 270 => 60
        assert self.cart.total(coupon="SAVE10") == round(270+60,2)

    def test_total_with_member_shipping_half(self):
        self.cart.add_item("e", 900.0, 1)   # subtotal 900
        # no coupon
        # shipping on 900 => 30 (member)
        assert self.cart.total(member=True) == round(900+30,2)

    def test_total_with_invalid_coupon_raises(self):
        self.cart.add_item("f", 50.0, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

    def test_total_empty_cart(self):
        assert self.cart.total() == 0.0
