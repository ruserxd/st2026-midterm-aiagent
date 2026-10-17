import pytest
import cart

# Test apply_discount
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# Test apply_discount raises ValueError for invalid inputs
@pytest.mark.parametrize("price,percent", [(-10, 10), (10, -5), (10, 105)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# Test bulk_discount_percent
@pytest.mark.parametrize("quantity,expected", [
    (1, 0),
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# Test bulk_discount_percent error
@pytest.mark.parametrize("quantity", [0, -5, 3.5])
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# Test parse_coupon
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    ("save20 ", 20),
    (" SAVE30", 30),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

# Test parse_coupon errors
@pytest.mark.parametrize("code", ["SAV10", "SAVE0", "SAVE51", "", "ABCD", " SAVE-5 "])
def test_parse_coupon_errors(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Test shipping_fee
@pytest.mark.parametrize("subtotal,member,expected", [
    (999, False, 60),
    (1000, False, 0),
    (1500, True, 0),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# shipping_fee errors
@pytest.mark.parametrize("subtotal", [-10, -1.5])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Test Cart class behavior
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_item(self):
        self.cart.add_item("apple", 1.00, 3)
        assert self.cart.items() == [("apple", 1.0, 3)]
        # adding same item increments quantity
        self.cart.add_item("apple", 1.00)
        assert self.cart.items() == [("apple", 1.0, 4)]

    def test_remove_item(self):
        self.cart.add_item("banana", 0.5, 5)
        self.cart.remove_item("banana", 2)
        assert self.cart.items() == [("banana", 0.5, 3)]
        # removing more than present removes item entirely
        self.cart.remove_item("banana", 5)
        assert self.cart.items() == []

    def test_subtotal(self):
        self.cart.add_item("item1", 10, 2)  # 20
        self.cart.add_item("item2", 5.5, 4)  # 22
        assert self.cart.subtotal() == 42.0

    def test_total_no_member_or_coupon(self):
        self.cart.add_item("widget", 30, 1)
        assert self.cart.total() == 90  # 30 + shipping 60

    def test_total_with_member_and_bulk_discount(self):
        self.cart.add_item("bulkitem", 100, 50)  # bulk discount 10%
        expected_subtotal = 100 * 50 * (1 - 0.10)
        assert self.cart.total(member=True) == round(expected_subtotal + 30, 2)

    def test_total_with_coupon(self):
        self.cart.add_item("couponitem", 200, 1)
        discount = cart.parse_coupon("SAVE20")
        expected_subtotal = 200 * (1 - discount/100.0)
        assert self.cart.total(coupon="SAVE20") == round(expected_subtotal + 60, 2)

    def test_total_with_member_and_coupon(self):
        self.cart.add_item("combo", 500, 1)
        # subtotal > 1000 shipping free
        assert self.cart.total(member=True, coupon="SAVE10") == round(500*(1-0.10)+0, 2)

    def test_total_invalid_coupon(self):
        self.cart.add_item("badcoupon", 50, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")
