import cart
import pytest

# ------------------------------
# Tests for apply_discount
# ------------------------------

def test_apply_discount_normal():
    assert cart.apply_discount(200, 15) == 170.0
    # rounding behaviour: e.g., 10% of 99 -> 89.1
    assert cart.apply_discount(99, 10) == round(99 * (100 - 10) / 100, 2)

@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError) as exc:
        cart.apply_discount(price, 10)
    assert "non-negative" in str(exc.value).lower()

@pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError) as exc:
        cart.apply_discount(100, percent)
    assert "between 0 and 100" in str(exc.value).lower()

# ------------------------------
# Tests for bulk_discount_percent
# ------------------------------

def test_bulk_discount_buckets():
    # bucket thresholds
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(50) == 10
    # note: quantity > 50 returns 10; test value 51
    assert cart.bulk_discount_percent(51) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@pytest.mark.parametrize("qty", [0, -3])
def test_bulk_discount_invalid_quantity_raises(qty):
    with pytest.raises(ValueError) as exc:
        cart.bulk_discount_percent(qty)
    assert "positive integer" in str(exc.value).lower()

# ------------------------------
# Tests for parse_coupon
# ------------------------------

def test_parse_coupon_valid_cases():
    # various forms
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon(" SAVE5 ") == 5

@pytest.mark.parametrize(
    "code",
    ["INVALID", "SAVE0", "SAVE51", "SAVExx", 123, None],
)
def test_parse_coupon_invalid_codes_raises(code):
    with pytest.raises(ValueError) as exc:
        cart.parse_coupon(code)
    assert "invalid coupon" in str(exc.value).lower() or "percent out of range" in str(exc.value).lower()

# ------------------------------
# Tests for shipping_fee
# ------------------------------

def test_shipping_free_over_threshold():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500, member=True) == 0

@pytest.mark.parametrize("subtotal", [-1, -50])
def test_shipping_negative_subtotal_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Non-member gets full fee below threshold
assert cart.shipping_fee(500) == 60
# Member gets half fee
assert cart.shipping_fee(500, member=True) == 30

# ------------------------------
# Tests for Cart class behaviours
# (Assuming typical implementation as per specification)
# ------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_subtotal(self):
        self.cart.add_item("apple", 100, quantity=3)
        assert self.cart.subtotal() == 300
        self.cart.add_item("apple", 100, quantity=2)
        assert self.cart.subtotal() == 500

    def test_remove_and_items(self):
        self.cart.add_item("banana", 50, quantity=5)
        self.cart.remove_item("banana", quantity=3)
        items = self.cart.items()
        # Expect remaining quantity of 2
        assert any(item["name"] == "banana" and item["quantity"] == 2 for item in items)

    def test_total_with_member_and_coupon(self):
        self.cart.add_item("widget", 200, quantity=10)  # qualifies for bulk discount 5%
        subtotal = self.cart.subtotal()  # 2000
        # apply bulk discount first: 5% off on items -\u003e 1900
        discounted_subtotal = cart.apply_discount(subtotal, 5)
        # coupon SAVE10 applies to discounted subtotal
        final_amount = cart.apply_discount(discounted_subtotal, 10)
        expected_total = final_amount + cart.shipping_fee(subtotal)  # member? no fee added separately
        assert self.cart.total(member=False, coupon="SAVE10") == pytest.approx(expected_total, rel=1e-9)

    def test_total_member_shipping_free_above_threshold(self):
        self.cart.add_item("mega", 1200, quantity=1)
        # subtotal >= threshold, shipping free even for non-member
        assert self.cart.total(member=True) == pytest.approx(1200.00, rel=1e-9)

    def test_total_invalid_coupon_raises(self):
        self.cart.add_item("thing", 100, quantity=2)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")
