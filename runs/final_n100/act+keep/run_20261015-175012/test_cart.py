import cart
import pytest

# Helper to round values as spec does (2 decimals)

def round2(x):
    return round(float(x), 2)

class TestCart:
    def test_empty_cart_total_zero(self):
        c = cart.Cart()
        assert c.total() == 0.00

    def test_subtotal_and_add_remove_items(self):
        c = cart.Cart()
        # Add items with different unit prices and quantities
        c.add_item('apple', 100, quantity=2)   # 200
        c.add_item('banana', 50)              # 50
        assert round2(c.subtotal()) == 250.00
        # Remove one banana
        c.remove_item('banana')
        assert round2(c.subtotal()) == 200.00
        # Remove one apple (reduces quantity to 1)
        c.remove_item('apple', quantity=1)
        assert round2(c.subtotal()) == 100.00
        # Removing non-existing item should raise KeyError
        with pytest.raises(KeyError):
            c.remove_item('pear')

    def test_shipping_fee_non_member_and_member(self):
        # Below threshold: fee = 60, member half
        assert cart.shipping_fee(500) == 60
        assert cart.shipping_fee(500, member=True) == 30
        # Above threshold: free shipping
        assert cart.shipping_fee(1000) == 0
        assert cart.shipping_fee(2000, member=True) == 0
        # Negative subtotal raises ValueError
        with pytest.raises(ValueError):
            cart.shipping_fee(-10)

    def test_coupon_parsing_valid_and_invalid(self):
        # Valid codes
        for code in ['SAVE5', 'save20', ' SAVE30 ', 'sAvE40']:
            percent = cart.parse_coupon(code)
            assert 1 <= percent <= 50
        # Invalid codes raise ValueError
        for bad in ['SAVEE10', 'SAVE0', 'SAVE51', 'random', '']:
            with pytest.raises(ValueError):
                cart.parse_coupon(bad)

    def test_total_with_coupon_and_shipping(self):
        c = cart.Cart()
        # Add items totaling 900 (below threshold)
        c.add_item('item1', 300, quantity=3)  # 900
        # Apply a valid coupon SAVE10 -> 10% off
        total_before_discount = 900.0
        discount = total_before_discount * 0.10
        subtotal_after_coupon = total_before_discount - discount
        expected_shipping = cart.shipping_fee(subtotal_after_coupon)
        expected_total = round2(subtotal_after_coupon + expected_shipping)
        assert c.total(coupon='SAVE10') == expected_total

    def test_total_without_coupon(self):
        c = cart.Cart()
        c.add_item('expensive', 1200)  # Above threshold, free shipping
        assert c.total() == round2(1200.00)

    def test_total_with_member_shipping_and_coupon(self):
        c = cart.Cart()
        c.add_item('medium', 400, quantity=2)  # subtotal 800
        # Coupon SAVE20 -> 20% off => 640
        expected_subtotal = 800.0 * 0.80
        shipping = cart.shipping_fee(expected_subtotal, member=True)
        assert shipping == 30  # because 800*0.8=640 <1000
        expected_total = round2(expected_subtotal + shipping)
        assert c.total(member=True, coupon='SAVE20') == expected_total

    def test_invalid_coupon_raises(self):
        c = cart.Cart()
        c.add_item('item', 100)
        with pytest.raises(ValueError):
            c.total(coupon='BADCODE')
