import pytest
import cart

# ---------- Utility functions ----------

def approx_equal(a, b, tol=1e-6):
    return abs(a - b) < tol

# ---------- Tests for helper functions ----------

class TestApplyDiscount:
    def test_valid_discount(self):
        assert cart.apply_discount(200, 15) == 170.0

    @pytest.mark.parametrize(
        "price, percent",
        [(-10, 5), (100, -1), (100, 101)],
    )
    def test_invalid_inputs(self, price, percent):
        with pytest.raises(ValueError):
            cart.apply_discount(price, percent)

class TestParseCoupon:
    def test_valid_codes(self):
        assert cart.parse_coupon("SAVE10") == 10
        assert cart.parse_coupon("save20 ") == 20

    @pytest.mark.parametrize(
        "code",
        ["SAVEBAD", "BAD10", "SAVE51", "save0", ""],
    )
    def test_invalid_codes(self, code):
        with pytest.raises(ValueError):
            cart.parse_coupon(code)

class TestShippingFee:
    def test_free_shipping_over_limit(self):
        assert cart.shipping_fee(1000) == 0
        assert cart.shipping_fee(1200.5) == 0

    def test_regular_shipping_for_non_members(self):
        assert cart.shipping_fee(999.99) == 60

    def test_half_shipping_for_members(self):
        assert cart.shipping_fee(500, member=True) == 30

    @pytest.mark.parametrize("subtotal", [-10, -0.01])
    def test_negative_subtotal_raises(self, subtotal):
        with pytest.raises(ValueError):
            cart.shipping_fee(subtotal)

# ---------- Tests for Cart class ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    # Helper to add item
    def add_item(self, name, price, quantity=1):
        self.cart.add_item(name, price, quantity)

    def test_add_and_subtotal_no_discount(self):
        self.add_item("Apple", 2.00, 3)  # 6.00
        assert self.cart.subtotal() == 6.00

    def test_bulk_discounts(self):
        # quantity 5 -> no discount
        self.add_item("Banana", 1.00, 5)
        assert self.cart.subtotal() == 5.00
        # quantity 10 -> 5% discount
        self.cart = cart.Cart()
        self.add_item("Banana", 1.00, 10)  # base 10.0, discount 5% => 9.5
        assert approx_equal(self.cart.subtotal(), 9.50)
        # quantity 55 -> 10% discount
        self.cart = cart.Cart()
        self.add_item("Cherry", 2.00, 55)  # base 110.0, discount 10% => 99.0
        assert approx_equal(self.cart.subtotal(), 99.0)
        # quantity 120 -> 15% discount
        self.cart = cart.Cart()
        self.add_item("Date", 3.00, 120)   # base 360.0, discount 15% => 306.0
        assert approx_equal(self.cart.subtotal(), 306.0)

    def test_add_duplicate_price_match(self):
        self.add_item("Eggs", 2.50, 1)
        self.add_item("Eggs", 2.50, 4)
        assert self.cart.items()["Eggs"] == 5

    def test_add_duplicate_price_mismatch_raises(self):
        self.add_item("Eggs", 2.50, 1)
        with pytest.raises(ValueError):
            self.add_item("Eggs", 3.00, 1)

    def test_remove_item_basic(self):
        self.add_item("Fig", 5.00, 3)
        self.cart.remove_item("Fig", 2)
        assert self.cart.items()["Fig"] == 1

    def test_remove_more_than_present_deletes(self):
        self.add_item("Grape", 4.00, 2)
        self.cart.remove_item("Grape", 5)  # should delete the item
        assert "Grape" not in self.cart.items()

    def test_remove_nonexistent_raises_keyerror(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("Honey")

    def test_total_no_items_returns_zero(self):
        assert self.cart.total() == 0

    def test_total_with_coupon_and_shipping(self):
        # subtotal = 200.00, coupon SAVE10 -> 180.00, shipping fee for non-member on 200 is 60
        self.add_item("Item", 100.00, 2)  # base 200
        total_amount = self.cart.total(coupon="SAVE10")
        expected_total = round(180 + 60, 2)
        assert total_amount == expected_total

    def test_member_shipping_half(self):
        self.add_item("Item", 50.00, 5)  # base 250
        total_nonmember = self.cart.total()
        total_member = self.cart.total(member=True)
        # shipping for subtotal 250: 60 -> member pays 30
        assert approx_equal(total_member, round(250 + 30, 2))
        assert total_nonmember == round(250 + 60, 2)

    def test_coupon_invalid_raises(self):
        self.add_item("Item", 100.00, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BAD")

# ---------- Edge case: shipping fee computed on discounted amount? (spec check) ----------
class TestShippingFeeSpec:
    def test_shipping_on_discounted_amount(self):
        # According to spec, shipping is based on subtotal AFTER coupon.
        # We set up a cart with 1000 subtotal and a valid coupon that would
        # normally reduce shipping to free. Implementation uses original subtotal,
        # so we detect the mismatch here.
        cart_obj = cart.Cart()
        cart_obj.add_item("Expensive", 500, 2)  # subtotal 1000
        # Subtotal >=1000 -> shipping should be free if coupon reduces amount
        # but implementation will still charge 60 because it uses original subtotal.
        total_with_coupon = cart_obj.total(coupon="SAVE10")
        # Expected: 900 after discount + 0 shipping = 900.00
        expected = round(900, 2)
        assert total_with_coupon == expected, (
            "Shipping fee should be free for subtotal >= 1000 even after coupon"
        )
