import pytest
import cart

# ---------- apply_discount -----------
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),          # example from spec
        (100, 0, 100.0),           # no discount
        (50, 100, 0.0),            # full discount
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price,percent",
    [(-1, 10), (100, -5), (100, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent -----------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -5, 3.2],
)
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon -----------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save25", 25),
        ("  Save50  ", 50),
    ],
)
def test_parse_coupon(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    ["SAV10", "SAVE0", "SAVE51", " SAVE51", "", "XMAS10"],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee -----------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (999.99, False, 60),
        (1000, False, 0),
        (1500, True, 30),
        (1200, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-1, -100],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class -----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_item_new_and_existing(self):
        self.cart.add_item("apple", 1.0, 3)
        assert self.cart.items() == {"apple": 3}
        self.cart.add_item("apple", 1.0, 2)
        assert self.cart.items() == {"apple": 5}

    def test_add_item_different_price_raises(self):
        self.cart.add_item("banana", 0.5, 2)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 0.6, 1)

    def test_remove_item_partial_and_all(self):
        self.cart.add_item("kiwi", 2.0, 5)
        self.cart.remove_item("kiwi", 3)
        assert self.cart.items() == {"kiwi": 2}
        self.cart.remove_item("kiwi", 2)
        assert "kiwi" not in self.cart.items()

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("peach")

    def test_subtotal_no_discount(self):
        self.cart.add_item("plum", 3.0, 4)
        assert self.cart.subtotal() == round(3.0 * 4, 2)

    def test_subtotal_with_bulk(self):
        self.cart.add_item("pear", 2.0, 10)  # triggers 5% bulk
        expected = cart.apply_discount(20.0, 5)
        assert self.cart.subtotal() == round(expected, 2)

    def test_total_without_coupon_member(self):
        self.cart.add_item("strawberry", 1.0, 20)  # 10% bulk
        amount = cart.apply_discount(20.0, 10)
        shipping = cart.shipping_fee(amount, False)
        expected = round(amount + shipping, 2)
        assert self.cart.total(member=False) == expected

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("blueberry", 5.0, 50)  # 10% bulk
        subtotal = cart.apply_discount(250.0, 10)
        after_coupon = cart.apply_discount(subtotal, cart.parse_coupon("SAVE20"))
        shipping = cart.shipping_fee(after_coupon, True)
        expected = round(after_coupon + shipping, 2)
        assert self.cart.total(member=True, coupon="SAVE20") == expected

    def test_total_empty_cart(self):
        assert self.cart.total() == 0

    def test_total_invalid_coupon_raises(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")

# The following tests will expose potential discrepancies in the implementation.
# They are designed to pass only if the implementation follows the specification exactly.

def test_cart_subtotal_discrepancy():
    cart_obj = cart.Cart()
    cart_obj.add_item("widget", 10.0, 1)
    # According to spec, subtotal is unit_price * quantity with bulk discount (none here)
    assert cart_obj.subtotal() == 10.0

# Test that shipping fee in total uses the discounted amount as specified.
def test_cart_total_shipping_behavior():
    cart_obj = cart.Cart()
    cart_obj.add_item("widget", 10.0, 1)
    # No coupon, no bulk discount
    # Expected shipping: 60 (subtotal 10 <1000, non-member)
    assert cart_obj.total() == round(10.0 + 60, 2)

# If a coupon is applied, total should use the discounted amount for shipping.
def test_cart_total_coupon_shipping():
    cart_obj = cart.Cart()
    cart_obj.add_item("widget", 100.0, 1)
    # subtotal 100 -> no bulk discount
    # apply coupon SAVE20 (20%) -> 80
    # shipping fee on 80 is 60 (still non-member)
    assert cart_obj.total(coupon="SAVE20") == round(80 + 60, 2)
