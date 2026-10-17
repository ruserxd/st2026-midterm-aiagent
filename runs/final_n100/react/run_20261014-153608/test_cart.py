import pytest
from cart import Cart, apply_discount, bulk_discount_percent, parse_coupon, shipping_fee

# Helper for discount calculation

def expect_discounted(amount, percent):
    return round(amount * (1 - percent / 100), 2)

class TestAddItem:
    def test_add_new_item(self):
        c = Cart()
        c.add_item("apple", 0.50, 3)
        assert c.items() == {"apple": 3}

    def test_add_existing_same_price_increases_quantity(self):
        c = Cart()
        c.add_item("banana", 0.30, 2)
        c.add_item("banana", 0.30, 1)
        assert c.items() == {"banana": 3}

    def test_add_existing_different_price_raises(self):
        c = Cart()
        c.add_item("orange", 0.60)
        with pytest.raises(ValueError):
            c.add_item("orange", 0.70)

    def test_negative_unit_price_raises(self):
        c = Cart()
        with pytest.raises(ValueError):
            c.add_item("pear", -1, 2)

    def test_non_positive_quantity_raises(self):
        c = Cart()
        with pytest.raises(ValueError):
            c.add_item("mango", 0.80, 0)

class TestRemoveItem:
    def test_remove_existing_item_reduces_quantity(self):
        c = Cart()
        c.add_item("apple", 1.00, 5)
        c.remove_item("apple", 2)
        assert c.items() == {"apple": 3}

    def test_remove_all_removes_item(self):
        c = Cart()
        c.add_item("banana", 0.50, 2)
        c.remove_item("banana", 2)
        assert "banana" not in c.items()

    def test_remove_more_than_quantity_removes_item(self):
        c = Cart()
        c.add_item("cherry", 0.20, 3)
        c.remove_item("cherry", 5)  # should remove the item entirely
        assert "cherry" not in c.items()

    def test_remove_nonexistent_raises(self):
        c = Cart()
        with pytest.raises(KeyError):
            c.remove_item("durian")

class TestSubtotal:
    def test_empty_cart_zero_subtotal(self):
        c = Cart()
        assert c.subtotal() == 0

    def test_no_discount_for_small_quantity(self, monkeypatch):
        # Assume bulk_discount_percent returns 0 for quantity < 5
        c = Cart()
        c.add_item("apple", 1.00, 3)
        assert c.subtotal() == expect_discounted(3.00, bulk_discount_percent(3))

    def test_bulk_discount_applied(self):
        c = Cart()
        c.add_item("bulk", 10.0, 6)  # quantity triggers discount
        line_total = 60.0
        discounted = apply_discount(line_total, bulk_discount_percent(6))
        assert c.subtotal() == round(discounted, 2)

class TestTotal:
    def test_empty_cart_zero(self):
        c = Cart()
        assert c.total() == 0

    def test_no_coupon_and_not_member_shipping_fee_applied(self, monkeypatch):
        # Stub shipping_fee to return a predictable value
        monkeypatch.setattr(cart, "shipping_fee", lambda subtotal, member=False: 5.00)
        c = Cart()
        c.add_item("item", 20.0, 2)  # subtotal 40
        expected_amount = apply_discount(40.0, bulk_discount_percent(2))
        total = round(expected_amount + 5.00, 2)
        assert c.total() == total

    def test_coupon_reduces_subtotal_before_shipping(self):
        c = Cart()
        c.add_item("item", 100.0, 1)
        # Suppose coupon code "SAVE10" gives 10% off
        with pytest.raises(ValueError):
            # First ensure invalid coupon raises
            c.total(coupon="INVALID")
        # Use a valid coupon; we mock parse_coupon to return 10%
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(cart, "parse_coupon", lambda code: 10 if code == "SAVE10" else ValueError("bad"))
        monkeypatch.setattr(cart, "shipping_fee", lambda subtotal, member=False: 5.00)
        amount_after_discount = apply_discount(100.0, 10)
        total_expected = round(amount_after_discount + 5.00, 2)
        assert c.total(coupon="SAVE10") == total_expected
        monkeypatch.undo()

    def test_member_shows_no_shipping_if_subtotal_above_threshold(self, monkeypatch):
        # Assume shipping_fee gives free shipping for subtotal >=50 when member=True
        monkeypatch.setattr(cart, "shipping_fee", lambda subtotal, member=False: 0.00 if member and subtotal >= 50 else 5.00)
        c = Cart()
        c.add_item("expensive", 30.0, 2)  # subtotal 60
        assert c.total(member=True) == round(60.0 + 0.00, 2)

    def test_non_member_always_ships(self):
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(cart, "shipping_fee", lambda subtotal, member=False: 5.00)
        c = Cart()
        c.add_item("stuff", 10.0, 1)
        assert c.total(member=False) == round(10.0 + 5.00, 2)
        monkeypatch.undo()
