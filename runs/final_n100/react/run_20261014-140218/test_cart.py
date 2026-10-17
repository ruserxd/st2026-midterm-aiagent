import pytest
import cart

# Helper function to create a cart with a single item

def make_cart(item_name="widget", unit_price=100.0, qty=1):
    c = cart.Cart()
    c.add_item(item_name, unit_price, qty)
    return c

class TestApplyDiscount:
    def test_basic(self):
        assert cart.apply_discount(200, 15) == 170.0

    def test_rounding(self):
        # 1% of 100 is 1 -> result 99.00
        assert cart.apply_discount(100, 1) == 99.0
        # ensure rounding to two decimals
        assert cart.apply_discount(123.456, 10) == round(111.1104, 2)

    def test_invalid_price(self):
        with pytest.raises(ValueError):
            cart.apply_discount(-5, 10)

    def test_invalid_percent(self):
        for p in [-1, 101]:
            with pytest.raises(ValueError):
                cart.apply_discount(100, p)

class TestBulkDiscountPercent:
    def test_no_discount(self):
        assert cart.bulk_discount_percent(5) == 0

    def test_ten_units(self):
        assert cart.bulk_discount_percent(10) == 5

    def test_fifty_units(self):
        assert cart.bulk_discount_percent(50) == 10

    def test_hundred_units(self):
        assert cart.bulk_discount_percent(100) == 15

    def test_invalid_quantity(self):
        for q in [0, -5]:
            with pytest.raises(ValueError):
                cart.bulk_discount_percent(q)

class TestParseCoupon:
    def test_valid_coupons(self):
        assert cart.parse_coupon("SAVE10") == 10
        assert cart.parse_coupon(" save20 ") == 20
        assert cart.parse_coupon("SaVe5") == 5

    def test_invalid_codes(self):
        for code in ["", "SAVExx", "DISCOUNT30", "save0", "save51"]:
            with pytest.raises(ValueError):
                cart.parse_coupon(code)

class TestShippingFee:
    def test_free_shipping(self):
        assert cart.shipping_fee(1000) == 0
        assert cart.shipping_fee(1500.50) == 0

    def test_regular_fee(self):
        assert cart.shipping_fee(999.99) == 60

    def test_member_half(self):
        assert cart.shipping_fee(500, member=True) == 30

    def test_invalid_subtotal(self):
        with pytest.raises(ValueError):
            cart.shipping_fee(-10)

class TestCart:
    def test_add_and_items(self):
        c = make_cart()
        assert c.items() == {"widget": (100.0, 1)}
        # add more quantity of same item
        c.add_item("widget", 100.0, 2)
        assert c.items()["widget"] == (100.0, 3)
        # add another item
        c.add_item("gadget", 200.0, 1)
        assert c.items() == {"widget": (100.0, 3), "gadget": (200.0, 1)}

    def test_remove(self):
        c = make_cart(qty=5)
        c.remove_item("widget", quantity=2)
        assert c.items()["widget"] == (100.0, 3)
        # removing more than existing quantity reduces to zero and removes key
        c.remove_item("widget", quantity=5)
        assert "widget" not in c.items()

    def test_subtotal(self):
        c = make_cart(qty=3)  # 3 * 100 = 300
        assert c.subtotal() == 300

    def test_total_no_coupon_member(self):
        c = make_cart(qty=2, unit_price=200)
        # subtotal 400; member => shipping half
        expected = 400 + 30  # 400*0.8 (20% discount?) no coupon
        assert c.total(member=True) == expected

    def test_total_with_coupon_and_bulk_discount(self):
        c = make_cart(item_name="item", unit_price=50, qty=10)
        # bulk discount for 10 items => 5%
        subtotal = 10 * 50
        discounted_subtotal = cart.apply_discount(subtotal, 5)
        shipping = cart.shipping_fee(discounted_subtotal)
        coupon = cart.parse_coupon("SAVE10")
        total_expected = discounted_subtotal + shipping
        total_expected = cart.apply_discount(total_expected, coupon)  # apply coupon after shipping
        assert c.total(coupon="SAVE10") == pytest.approx(total_expected)

    def test_total_free_shipping(self):
        c = make_cart(item_name="expensive", unit_price=2000, qty=1)
        # subtotal >1000 => free shipping
        assert c.total() == 2000
