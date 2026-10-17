import pytest
import cart

# apply_discount tests
def test_apply_discount_basic():
    # Basic cases for apply_discount
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(100, 100) == 0.0

@ pytest.mark.parametrize("price,percent", [(-10, 10), (50, -5), (50, 105)])
# test error cases for apply_discount
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent tests
def test_bulk_discount_percent():
    # Quantities and expected discounts
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("quantity", [0, -1, "ten"])
# test error cases for bulk_discount_percent
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests
def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save25") == 25
    assert cart.parse_coupon("  SaVe50 ") == 50
    assert cart.parse_coupon("SaVe1") == 1

@ pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "DISCOUNT10", "", "   "])
# test error cases for parse_coupon
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
def test_shipping_fee():
    assert cart.shipping_fee(500.0, False) == 60
    assert cart.shipping_fee(500.0, True) == 30
    assert cart.shipping_fee(1000.0, False) == 0
    assert cart.shipping_fee(1500.0, True) == 0

@ pytest.mark.parametrize("subtotal", [-10.0, -1])
# test error cases for shipping_fee
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart tests
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_initialization(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0
        assert self.cart.total() == 0

    def test_add_item_new_and_existing(self):
        self.cart.add_item("apple", 1.00, 3)
        assert self.cart.items() == {"apple": 3}
        # add same item with correct price increases quantity
        self.cart.add_item("apple", 1.00, 2)
        assert self.cart.items() == {"apple": 5}

    def test_add_item_invalid_price_quantity(self):
        with pytest.raises(ValueError):
            self.cart.add_item("banana", -1.0, 3)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 1.0, 0)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 1.0, -2)

    def test_add_item_price_mismatch(self):
        self.cart.add_item("orange", 1.5, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 2.0, 1)

    def test_remove_item_reduce_and_remove(self):
        self.cart.add_item("mango", 2.0, 4)
        # remove part
        self.cart.remove_item("mango", 2)
        assert self.cart.items() == {"mango": 2}
        # remove remaining
        self.cart.remove_item("mango", 2)
        assert self.cart.items() == {}

    def test_remove_more_than_quantity(self):
        self.cart.add_item("kiwi", 3.0, 1)
        # removing more than present should still remove item
        self.cart.remove_item("kiwi", 5)
        assert self.cart.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("papaya", 1)

    def test_items_returns_copy(self):
        self.cart.add_item("peach", 2.0, 2)
        items = self.cart.items()
        items["peach"] = 10
        assert self.cart.items() == {"peach": 2}

    def test_subtotal_no_discount_and_with_discount(self):
        # item without discount: quantity <10
        self.cart.add_item("strawberry", 1.0, 5)
        # item with bulk discount: quantity >=10
        self.cart.add_item("blueberry", 2.0, 12)  # 5% discount
        strawberry_sub = 5 * 1.0
        blueberry_total = 12 * 2.0
        blueberry_discount = blueberry_total * 0.05
        blueberry_net = blueberry_total - blueberry_discount
        expected = round(strawberry_sub + blueberry_net, 2)
        assert self.cart.subtotal() == expected

    def test_subtotal_empty(self):
        empty_cart = cart.Cart()
        assert empty_cart.subtotal() == 0

    def test_total_no_coupon_member_status(self):
        # setup cart with known items
        self.cart.add_item("strawberry", 1.0, 5)     # no discount: 5
        self.cart.add_item("blueberry", 2.0, 12)     # 5% discount on 24 => net 22.8
        subtotal_expected = round(5 + 22.8, 2)
        assert self.cart.subtotal() == subtotal_expected

        # total with no coupon, non-member shipping fee 60
        expected_total_nonmember = round(subtotal_expected + 60, 2)
        assert self.cart.total(member=False) == expected_total_nonmember

        # member gets half shipping
        expected_total_member = round(subtotal_expected + 30, 2)
        assert self.cart.total(member=True) == expected_total_member

    def test_total_with_coupon(self):
        self.cart = cart.Cart()
        self.cart.add_item("strawberry", 1.0, 5)     # subtotal part: 5
        self.cart.add_item("blueberry", 2.0, 12)     # net 22.8 => subtotal 27.8

        subtotal = round(5 + 22.8, 2)
        coupon_percent = cart.parse_coupon("SAVE10")  # 10%
        after_coupon = round(subtotal * (1 - coupon_percent/100), 2)

        shipping_fee = 60   # non-member
        expected_total = round(after_coupon + shipping_fee, 2)
        assert self.cart.total(coupon="SAVE10", member=False) == expected_total

    def test_total_invalid_coupon(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")

    def test_total_empty_cart_no_shipping(self):
        empty = cart.Cart()
        assert empty.total() == 0
