import cart
import pytest

# Helper to create cart with simple item dicts
def make_cart(items):
    return cart.Cart(items)

class TestParseCoupon:
    def test_valid_codes(self):
        # Only uppercase codes are valid as per implementation.
        for code, percent in [("SAVE10", 10), ("SAVE20", 20)]:
            assert cart.parse_coupon(code) == percent

    def test_invalid_codes(self):
        invalid = ["SAVEX", "SAVE0", "SAVE51", "X123", "", "   "]
        for code in invalid:
            with pytest.raises(ValueError):
                cart.parse_coupon(code)

class TestCartTotal:
    def test_empty_cart(self):
        c = make_cart([])
        assert c.total() == 0

    def test_no_coupons_shipping_fee(self):
        items = [{"name": "Apple", "price": 1.00, "quantity": 2}, {"name": "Bread", "price": 2.50}]
        c = make_cart(items)
        subtotal = sum(item["price"] * item.get("quantity",1) for item in items)
        shipping = c.shipping_fee()
        expected = round(subtotal + shipping, 2)
        assert c.total() == expected

    def test_with_valid_coupon(self):
        items = [{"name": "Apple", "price": 1.00, "quantity": 5}]
        c = make_cart(items)
        subtotal = sum(item["price"] * item.get("quantity",1) for item in items)
        discount = cart.parse_coupon("SAVE10")
        discounted_total = subtotal * (1 - discount/100)
        shipping = c.shipping_fee()
        expected = round(discounted_total + shipping, 2)
        assert c.total("SAVE10") == expected

    def test_invalid_coupon_raises(self):
        items = [{"name": "Apple", "price": 1.00}]
        c = make_cart(items)
        with pytest.raises(ValueError):
            c.total("INVALIDCODE")
