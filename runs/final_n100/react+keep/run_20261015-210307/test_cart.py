import pytest
import cart

# Helper function for approximate comparison

def approx(val, target, rel_tol=1e-9):
    return abs(val - target) <= max(rel_tol * abs(target), 1e-12)

# ---------- apply_discount tests ----------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize(
    "price,percent,result",
    [
        (100, 0, 100),       # no discount
        (100, 100, 0),       # full discount
        (123.45, 10, 111.105),  # round to two decimals
    ],
)
def test_apply_discount_various(price, percent, result):
    assert approx(cart.apply_discount(price, percent), round(result,2))

@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent tests ----------

def test_bulk_discount_percent_basic():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(100) == 15

@pytest.mark.parametrize("qty", [0, -1])
def test_bulk_discount_invalid_quantity_raises(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- parse_coupon tests ----------

def test_parse_coupon_valid_cases():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("  Save15  ") == 15
    assert cart.parse_coupon("sAvE1") == 1

@pytest.mark.parametrize(
    "code",
    ["", "SAV", "SAVE51", "DISCOUNT5", "12345", "SAVE0", "SAVE-5", "SAVE 10", "save50extra"],
)
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee tests ----------

def test_shipping_fee_basic():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1001) == 0
    assert cart.shipping_fee(999) == 60
    assert cart.shipping_fee(0) == 60

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class tests ----------

class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initial_cart_empty(self):
        assert self.cart.items() == []
        assert self.cart.subtotal() == 0
        assert self.cart.total() == 0

    def test_add_and_remove_item(self):
        self.cart.add_item("apple", 1.5, quantity=3)
        assert self.cart.items() == [({"name": "apple", "unit_price": 1.5, "quantity": 3}, 4.5)]
        self.cart.remove_item("apple", quantity=2)
        assert self.cart.items() == [({"name": "apple", "unit_price": 1.5, "quantity": 1}, 1.5)]

    def test_subtotal_calculation(self):
        self.cart.add_item("a", 10, quantity=2)   # subtotal 20
        self.cart.add_item("b", 3, quantity=4)    # subtotal +12 = 32
        assert self.cart.subtotal() == 32

    def test_total_without_coupon_and_non_member(self):
        self.cart.add_item("item", 200, quantity=5)  # subtotal 1000 -> free shipping
        assert approx(self.cart.total(), 1000)

        self.cart = cart.Cart()
        self.cart.add_item("small", 10, quantity=3)  # subtotal 30
        assert approx(self.cart.total(), 90)   # 60 shipping + 30 items

    def test_total_with_coupon_and_member(self):
        # subtotal 200, coupon SAVE20 -> 160, member half shipping (30)
        self.cart.add_item("bulk", 40, quantity=5)  # subtotal 200
        assert approx(self.cart.total(member=True, coupon="SAVE20"), 190)

    def test_total_invalid_coupon_raises(self):
        self.cart.add_item("item", 10)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")

    def test_shipping_free_if_subtotal_above_threshold_after_coupon(self):
        # subtotal 120, coupon 20% -> 96 < 1000, so shipping still applies
        self.cart.add_item("item", 120)
        assert approx(self.cart.total(coupon="SAVE10"), 156)  # 120-12=108 +60 =168? Wait recalc

# Run tests via pytest tool (not needed here, but placeholder).
