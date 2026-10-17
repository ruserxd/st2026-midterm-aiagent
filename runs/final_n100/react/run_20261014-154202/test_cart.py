import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# -------------------------------------------------------------------
# Helper function tests – they exercise the specification directly.
# -------------------------------------------------------------------

class TestApplyDiscount:
    def test_basic_reduction(self):
        assert apply_discount(200, 15) == 170.0

    def test_no_percent(self):
        assert apply_discount(100, 0) == 100.0

    def test_full_percent(self):
        assert apply_discount(50, 100) == 0.0

    @pytest.mark.parametrize("price,percent", [(-1,10),(50,-5),(50,110)])
    def test_invalid_inputs(self, price, percent):
        with pytest.raises(ValueError):
            apply_discount(price, percent)

class TestBulkDiscountPercent:
    def test_quantities_and_discounts(self):
        assert bulk_discount_percent(9) == 0
        assert bulk_discount_percent(10) == 5
        assert bulk_discount_percent(49) == 5
        assert bulk_discount_percent(50) == 10
        assert bulk_discount_percent(99) == 10
        assert bulk_discount_percent(100) == 15
        assert bulk_discount_percent(500) == 15

    @pytest.mark.parametrize("quantity", [0,-1,3.5])
    def test_invalid_quantity(self, quantity):
        with pytest.raises(ValueError):
            bulk_discount_percent(quantity)

class TestParseCoupon:
    def test_valid_codes_case_insensitive_and_spaces(self):
        assert parse_coupon("SAVE10") == 10
        assert parse_coupon("save10") == 10
        assert parse_coupon("  SaVe25 ") == 25

    @pytest.mark.parametrize(
        "code",
        ["SAVE0", "SAVE51", "SAVE-5", "ABC10", "SAVEE"]
    )
    def test_invalid_codes(self, code):
        with pytest.raises(ValueError):
            parse_coupon(code)

class TestShippingFee:
    def test_free_and_regular_fee(self):
        assert shipping_fee(999) == 60
        assert shipping_fee(1000) == 0
        assert shipping_fee(1200) == 0

    def test_member_discount(self):
        assert shipping_fee(500, member=True) == 30
        assert shipping_fee(1500, member=True) == 0

    @pytest.mark.parametrize("subtotal", [-1, -50])
    def test_invalid_subtotal(self, subtotal):
        with pytest.raises(ValueError):
            shipping_fee(subtotal)

# -------------------------------------------------------------------
# Cart class tests – they rely on the specification but are tolerant of
# different iterable structures returned by `items()`.
# -------------------------------------------------------------------

class TestCart:
    def setup_method(self):
        self.cart = Cart()

    def test_initial_state_empty(self):
        # items() may return an iterator of tuples or objects; we only
        # care that it is empty.
        assert list(self.cart.items()) == []
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    def _items_dict(self, cart):
        """Return a mapping of name->quantity from the cart's items.
        The cart may expose items in many formats; this helper normalises
        them to tuples ``(name, qty)`` for consistency.
        """
        result = {}
        for item in cart.items():
            try:
                # Assume the item is a tuple/list of two elements
                name, qty = item
            except Exception:
                # Fallback: try to use attributes or keys if available
                if hasattr(item, "name") and hasattr(item, "quantity"):
                    name, qty = item.name, item.quantity
                else:
                    raise
            result[name] = qty
        return result

    def test_add_item_single_and_multiple_quantities(self):
        self.cart.add_item("apple", 10, quantity=2)
        self.cart.add_item("banana", 5)
        # Adding again should sum quantities
        self.cart.add_item("apple", 10, quantity=3)
        items = self._items_dict(self.cart)
        assert items == {"apple": 5, "banana": 1}
        assert self.cart.subtotal() == 10 * 5 + 5 * 1

    def test_remove_item_partial_and_full(self):
        self.cart.add_item("orange", 8, quantity=4)
        self.cart.remove_item("orange", quantity=2)
        items = self._items_dict(self.cart)
        assert items["orange"] == 2
        # Removing more than existing should remove the item entirely
        self.cart.remove_item("orange", quantity=5)
        assert "orange" not in self._items_dict(self.cart)

    def test_subtotal_and_total_with_coupons_and_shipping(self):
        # Populate cart with items crossing bulk discount thresholds.
        self.cart.add_item("widget", 20, quantity=120)  # 20*120 = 2400 before discounts
        assert self.cart.subtotal() == 2400.0
        # Compute expected total: apply bulk discount (15%) first
        after_bulk = apply_discount(self.cart.subtotal(), bulk_discount_percent(120))
        # Now apply a coupon if desired
        no_coupon_total = round(after_bulk + shipping_fee(after_bulk), 2)
        assert self.cart.total() == no_coupon_total
        # With a valid coupon and member status
        after_coupon = apply_discount(after_bulk, parse_coupon("SAVE20"))
        total_with_coupon_member = round(
            after_coupon + shipping_fee(after_coupon, member=True), 2
        )
        assert self.cart.total(member=True, coupon="SAVE20") == total_with_coupon_member

    def test_invalid_coupon_in_total(self):
        self.cart.add_item("gadget", 30)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

    def test_member_shipment_free_threshold_after_coupons(self):
        # Cart subtotal is just below free threshold after coupon application
        self.cart.add_item("thing", 10, quantity=100)  # 1000 total before discount
        # Apply a 5% coupon -> 950, still not free shipping
        expected = round(
            apply_discount(950, parse_coupon("SAVE5")) + shipping_fee(apply_discount(950, parse_coupon("SAVE5")))
            , 2)
        assert self.cart.total(coupon="SAVE5") == pytest.approx(expected)
        # Apply a 20% coupon -> 800, still not free
        expected = round(
            apply_discount(800, parse_coupon("SAVE20")) + shipping_fee(apply_discount(800, parse_coupon("SAVE20")))
            , 2)
        assert self.cart.total(coupon="SAVE20") == pytest.approx(expected)

    def test_empty_cart_total_no_shipping(self):
        # Empty cart: total should be zero regardless of coupon or member flag
        assert self.cart.total(member=True, coupon="SAVE10") == 0.0

if __name__ == "__main__":
    pytest.main(["-q"])
