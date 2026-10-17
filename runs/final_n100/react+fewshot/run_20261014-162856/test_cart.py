import pytest
import cart

# ---------- apply_discount ---------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    # percent rounding check
    assert cart.apply_discount(100, 33) == round(100 * (1 - 33 / 100), 2)

@pytest.mark.parametrize("price", [-10, -0.01])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 20)

@pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(50, percent)

# ---------- bulk_discount_percent ---------------------------

def test_bulk_discount_basic():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

@pytest.mark.parametrize("quantity", [0, -3])
def test_bulk_discount_invalid_quantity_raises(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon -----------------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon("  SaVe30 ") == 30

@pytest.mark.parametrize(
    "code",
    ["SAVE0", "SAVE51", "DISCOUNT10", "save-5", "SAVExx", ""]
)
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee -----------------------------------

def test_shipping_fee_basic():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0

# member pays half
assert cart.shipping_fee(500, member=True) == 30
assert cart.shipping_fee(1200, member=True) == 0

@pytest.mark.parametrize("subtotal", [-1.5, -0.01])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class -------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    # --- add_item -------------------------------------------------
    def test_add_new_item_increases_quantity_and_price(self):
        self.cart.add_item("apple", 1.00, quantity=2)
        assert self.cart.items() == {"apple": 2}
        assert self.cart.subtotal() == round(1.00 * 2 * (1 - 0/100), 2)

    def test_add_existing_item_increases_quantity(self):
        self.cart.add_item("banana", 0.50, quantity=3)
        self.cart.add_item("banana", 0.50, quantity=2)
        assert self.cart.items() == {"banana": 5}

    def test_add_existing_item_different_price_raises(self):
        self.cart.add_item("orange", 1.20, quantity=1)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 1.25, quantity=1)

    @pytest.mark.parametrize("unit_price", [-5, -0.01])
    def test_add_item_negative_price_raises(self, unit_price):
        with pytest.raises(ValueError):
            self.cart.add_item("pear", unit_price, quantity=2)

    @pytest.mark.parametrize("quantity", [0, -3])
    def test_add_item_invalid_quantity_raises(self, quantity):
        with pytest.raises(ValueError):
            self.cart.add_item("kiwi", 2.00, quantity=quantity)

    # --- remove_item -----------------------------------------------
    def test_remove_partial_quantity(self):
        self.cart.add_item("mango", 3.00, quantity=4)
        self.cart.remove_item("mango", quantity=1)
        assert self.cart.items() == {"mango": 3}

    def test_remove_entire_quantity_removes_item(self):
        self.cart.add_item("peach", 2.50, quantity=2)
        self.cart.remove_item("peach", quantity=2)
        assert "peach" not in self.cart.items()

    def test_remove_more_than_exists_leaves_empty_and_removes(self):
        self.cart.add_item("plum", 1.75, quantity=3)
        self.cart.remove_item("plum", quantity=5)  # should remove the item
        assert "plum" not in self.cart.items()

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent", quantity=1)

    # --- subtotal --------------------------------------------------
    def test_subtotal_bulk_discount_applied_per_item(self):
        # 12 bananas -> bulk discount 5%
        self.cart.add_item("banana", 0.50, quantity=12)
        expected = round(0.50 * 12 * (1 - 5/100), 2)
        assert self.cart.subtotal() == expected

    def test_subtotal_empty_cart(self):
        assert self.cart.subtotal() == 0

    # --- total -----------------------------------------------------
    def test_total_without_coupon_or_member(self):
        self.cart.add_item("cherry", 2.00, quantity=3)  # no bulk discount
        subtotal = round(2.00 * 3, 2)
        shipping = cart.shipping_fee(subtotal)
        expected = round(subtotal + shipping, 2)
        assert self.cart.total() == expected

    def test_total_with_coupon(self):
        self.cart.add_item("donut", 1.50, quantity=4)  # no bulk discount
        subtotal = round(1.50 * 4, 2)
        after_coupon = round(subtotal * (1 - cart.parse_coupon("SAVE10") / 100), 2)
        shipping = cart.shipping_fee(after_coupon)
        expected = round(after_coupon + shipping, 2)
        assert self.cart.total(coupon="SAVE10") == expected

    def test_total_with_invalid_coupon_raises(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")

    def test_total_for_member_discount_shipping_half(self):
        self.cart.add_item("eclair", 5.00, quantity=1)
        subtotal = round(5.00 * 1, 2)
        shipping_fee = cart.shipping_fee(subtotal, member=True)
        expected = round(subtotal + shipping_fee, 2)
        assert self.cart.total(member=True) == expected

    def test_total_empty_cart_zero(self):
        assert self.cart.total() == 0
