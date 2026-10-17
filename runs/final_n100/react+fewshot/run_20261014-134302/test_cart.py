import pytest
import cart

# ---------- apply_discount -------------------------------------------------

def test_apply_discount_valid_cases():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0
    # rounding: 99.999 -> should round to two decimals
    assert cart.apply_discount(199.995, 10) == 179.9965
    # but rounding applied after subtraction
    assert round(cart.apply_discount(199.995, 10), 2) == 179.9965

@patch

def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        cart.apply_discount(-1, 10)

@patch

def test_apply_discount_invalid_percent():
    with pytest.raises(ValueError):
        cart.apply_discount(100, -5)
    with pytest.raises(ValueError):
        cart.apply_discount(100, 105)

# ---------- bulk_discount_percent ------------------------------------------

def test_bulk_discount_percent_cases():
    assert cart.bulk_discount_percent(1) == 0
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@patch

def test_bulk_discount_percent_invalid():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-1)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0.5)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent("10")

# ---------- parse_coupon ----------------------------------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save25") == 25
    assert cart.parse_coupon("   SaVe50  ") == 50
    # lower bound
    assert cart.parse_coupon("savE1") == 1

@patch

def test_parse_coupon_invalid():
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE0")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE51")
    with pytest.raises(ValueError):
        cart.parse_coupon("NOTACODE")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE-5")

# ---------- shipping_fee -----------------------------------------------------

def test_shipping_fee_free_and_standard():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(2000) == 0

# member half fee
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(1500, member=True) == 0

@patch

def test_shipping_fee_invalid_subtotal():
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

# ---------- Cart class -------------------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initial_state(self):
        assert isinstance(self.cart.items(), dict)
        assert len(self.cart.items()) == 0
        assert self.cart.subtotal() == 0
        assert self.cart.total() == 0

    def test_add_item_new(self):
        self.cart.add_item("apple", 1.00, 3)
        assert self.cart.items() == {"apple": 3}
        # unit price check via subtotal calculation
        assert self.cart.subtotal() == round(1.0 * 3 * (100 - cart.bulk_discount_percent(3)) / 100, 2)

    def test_add_item_existing_same_price(self):
        self.cart.add_item("banana", 0.50, 2)
        self.cart.add_item("banana", 0.50, 1)
        assert self.cart.items() == {"banana": 3}

    @patch
    def test_add_item_existing_diff_price(self):
        self.cart.add_item("orange", 0.80, 2)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 1.00, 1)

    @patch
    def test_add_invalid_unit_price_and_quantity(self):
        with pytest.raises(ValueError):
            self.cart.add_item("mango", -0.5, 2)
        with pytest.raises(ValueError):
            self.cart.add_item("mango", 1.00, 0)
        with pytest.raises(ValueError):
            self.cart.add_item("mango", 1.00, -3)

    def test_remove_item_partial_and_full(self):
        self.cart.add_item("peach", 2.00, 5)
        self.cart.remove_item("peach", 2)
        assert self.cart.items() == {"peach": 3}
        # remove remaining
        self.cart.remove_item("peach", 3)
        assert "peach" not in self.cart.items()

    @patch
    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexist", 1)

    def test_subtotal_bulk_discount_application(self):
        # 10 units should trigger 5% discount, 50 units -> 10%, 100 units ->15%
        self.cart.add_item("item1", 10.00, 9)   # no discount
        self.cart.add_item("item2", 20.00, 10)  # 5% off
        self.cart.add_item("item3", 30.00, 50)  # 10% off
        self.cart.add_item("item4", 40.00, 100) # 15% off
        subtotal = (
            9 * 10.00 +
            10 * 20.00 * (95 / 100) +
            50 * 30.00 * (90 / 100) +
            100 * 40.00 * (85 / 100)
        )
        assert self.cart.subtotal() == round(subtotal, 2)

    def test_total_without_coupon_or_member(self):
        self.cart.add_item("item", 20.00, 1)
        # subtotal = 20.00; shipping fee = 60 -> total 80.00
        assert self.cart.total() == round(20.00 + 60, 2)

    def test_total_with_member_discount(self):
        self.cart.add_item("item", 1000.00, 1)  # subtotal >= 1000 -> free shipping
        # member doesn't affect because shipping already free
        assert self.cart.total(member=True) == round(1000.00 + 0, 2)

    def test_total_with_coupon(self):
        self.cart.add_item("item", 200.00, 1)
        total_before = self.cart.subtotal() + cart.shipping_fee(self.cart.subtotal())
        # apply 10% coupon
        expected = round(total_before * (90 / 100), 2)
        assert self.cart.total(coupon="SAVE10") == expected

    def test_total_with_invalid_coupon_raises(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

    def test_empty_cart_no_shipping(self):
        assert self.cart.total() == 0

# ---------- End of tests ----------------------------------------------"
