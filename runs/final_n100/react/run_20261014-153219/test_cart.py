import pytest
from cart import Cart, apply_discount, bulk_discount_percent, parse_coupon, shipping_fee

# ---- Helper constants from specification ----
UNIT_PRICE = 10.0
QUANTITY1 = 2
QUANTITY5 = 5
DISCOUNT_PERCENT = 20
CURRENCY_PRECISION=2

class TestApplyDiscount:
    def test_basic_discount(self):
        assert apply_discount(100, 20) == pytest.approx(80.00)

    def test_zero_percent(self):
        assert apply_discount(50, 0) == pytest.approx(50.00)

    def test_full_percent(self):
        assert apply_discount(200, 100) == pytest.approx(0.00)

class TestBulkDiscountPercent:
    def test_no_bulk(self):
        assert bulk_discount_percent(3) == 0

    def test_threshold_5(self):
        # Quantity exactly at threshold
        assert bulk_discount_percent(5) == 1

    def test_above_threshold(self):
        assert bulk_discount_percent(10) == 2

class TestParseCoupon:
    def test_valid_code_with_discount(self):
        code = 'SAVE20-1234'
        expected = {
            "code": "SAVE20-1234",
            "coupon_type": "percentage",
            "value": 20,
            "expires_on": None
        }
        assert parse_coupon(code) == expected

    def test_valid_code_with_free_shipping(self):
        code = 'FREESHIP-5678'
        expected = {
            "code": "FREESHIP-5678",
            "coupon_type": "shipping",
            "value": None,
            "expires_on": None
        }
        assert parse_coupon(code) == expected

    def test_invalid_code(self):
        with pytest.raises(ValueError):
            parse_coupon('INVALID')

class TestShippingFee:
    def test_standard_fee(self):
        assert shipping_fee(30.0, member=False) == pytest.approx(5.00)

    def test_member_discounted(self):
        assert shipping_fee(30.0, member=True) == pytest.approx(3.00)

    def test_free_shipping_threshold(self):
        # Subtotal exceeds free shipping threshold (assumed 50 in spec?)
        assert shipping_fee(60.0, member=False) == pytest.approx(0.00)

class TestCart:
    @pytest.fixture
    def cart(self):
        return Cart()

    def test_add_and_items(self, cart):
        cart.add_item('apple', 1.5, quantity=3)
        assert cart.items() == {'apple': (1.5, 3)}

    def test_remove_item_partial(self, cart):
        cart.add_item('banana', 0.75, quantity=5)
        cart.remove_item('banana', quantity=2)
        assert cart.items()['banana'][1] == 3

    def test_remove_item_complete(self, cart):
        cart.add_item('orange', 0.6, quantity=4)
        cart.remove_item('orange', quantity=4)
        assert 'orange' not in cart.items()

    def test_subtotal_calculation(self, cart):
        cart.add_item('book', 12.0, quantity=2)
        cart.add_item('pen', 1.25, quantity=3)
        expected = 12.0*2 + 1.25*3
        assert cart.subtotal() == pytest.approx(expected)

    def test_total_with_bulk_discount(self, cart):
        # Adding 5 units triggers bulk discount of 1%
        cart.add_item('tshirt', 20.0, quantity=5)
        total = cart.total()
        expected_subtotal = 20.0*5
        discounted_price = apply_discount(expected_subtotal, 1)
        assert total == pytest.approx(discounted_price + shipping_fee(expected_subtotal))

    def test_total_with_coupon_and_member(self, cart):
        cart.add_item('headphones', 50.0)
        coupon = {'code': 'SAVE10-0001', 'coupon_type': 'percentage', 'value': 10, 'expires_on': None}
        total = cart.total(member=True, coupon=coupon)
        # subtotal
        sub = 50.0
        # member discount on shipping
        ship = shipping_fee(sub, member=True)
        # apply coupon percent
        after_coupon = apply_discount(sub + ship, 10)
        assert total == pytest.approx(after_coupon)
