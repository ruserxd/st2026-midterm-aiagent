import pytest
import cart

# ---------- apply_discount -------------------------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (100, 0, 100.0),
        (50, 100, 0.0),
        (123.45, 25, 92.58),  # 123.45 * 0.75 = 92.5875 -> rounded
    ],
)
def test_apply_discount_various(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@ pytest.mark.parametrize("price", [-1, -10])
@ pytest.mark.parametrize("percent", [0])
# actually check error for negative price

def test_apply_discount_invalid_price(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

@pytest.mark.parametrize(
    "price, percent",
    [(100, -1), (200, 101), (50, 150)],
)
def test_apply_discount_invalid_percent(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ------------------------------------------

def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(15) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(200) == 15

@ pytest.mark.parametrize("quantity", [0, -1])
# invalid quantity should raise ValueError

def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon -----------------------------------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20 ") == 20
    assert cart.parse_coupon("  SaVe50") == 50

@ pytest.mark.parametrize(
    "code",
    ["", "SAVEX", "SAVE0", "SAVE51", "ABCD", "123", " SAVE10a"],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee -----------------------------------------------------

def test_shipping_fee_non_member():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(500) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(2000) == 0

def test_shipping_fee_member():
    assert cart.shipping_fee(0, member=True) == 30
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(999.99, member=True) == 30
    assert cart.shipping_fee(1000, member=True) == 0

@ pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class -------------------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_totals(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0
        # total with no shipping for empty cart
        assert self.cart.total() == 0.0
        assert self.cart.total(member=True) == 0.0

    def test_add_and_remove_items(self):
        self.cart.add_item("apple", 100, 2)
        assert self.cart.items() == {"apple": 2}
        # adding same item increases quantity but same unit price
        self.cart.add_item("apple", 100, 3)
        assert self.cart.items() == {"apple": 5}
        # bulk discount for 5 units -> 0%
        assert self.cart.subtotal() == 500.0
        # add second item
        self.cart.add_item("banana", 50, 10)  # 10 -> 5% discount on banana
        assert self.cart.items() == {"apple": 5, "banana": 10}
        # subtotal calculation: apple 500 + banana 50*10*0.95 = 475
        assert self.cart.subtotal() == 975.0
        # total without coupon or member
        expected_total = 975.0 + cart.shipping_fee(975.0)
        assert self.cart.total() == round(expected_total, 2)

    def test_add_item_invalid(self):
        with pytest.raises(ValueError):
            self.cart.add_item("orange", -5, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 10, 0)
        # unit price mismatch
        self.cart.add_item("pear", 20, 2)
        with pytest.raises(ValueError):
            self.cart.add_item("pear", 25, 1)

    def test_remove_items(self):
        self.cart.add_item("item", 10, 5)
        # remove less than quantity
        self.cart.remove_item("item", 2)
        assert self.cart.items() == {"item": 3}
        # remove remaining -> item removed
        self.cart.remove_item("item", 3)
        assert self.cart.items() == {}
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent", 1)

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("widget", 200, 10)  # bulk discount 5%
        subtotal = cart.apply_discount(200*10, 5)  # 2000 *0.95=1900
        assert self.cart.subtotal() == 1900.0
        total_no_coupon = round(subtotal + cart.shipping_fee(subtotal), 2)
        assert self.cart.total(member=True) == total_no_coupon
        # coupon 20%
        total_with_coupon = round(cart.apply_discount(total_no_coupon, 20), 2)
        assert self.cart.total(coupon="SAVE20") == total_with_coupon
        # invalid coupon should raise
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")
