import pytest
import cart

# Helper function to round floats as expected

def _approx_equal(a, b, tol=1e-2):
    return abs(a - b) <= tol

# ---------- apply_discount tests ----------
@pytest.mark.parametrize("price, percent, expected", [
    (200.0, 15, 170.0),
    (100.0, 0, 100.0),
    (50.0, 100, 0.0),
])
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price, percent", [
    (-1, 10),
    (10, -5),
    (10, 105),
])
def test_apply_discount_invalid_args(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent tests ----------
@pytest.mark.parametrize("quantity, expected", [
    (5, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 1.5, "a"])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon tests ----------
@pytest.mark.parametrize("code, expected", [
    ("SAVE10", 10),
    (" save25 ", 25),
    ("sAvE5", 5),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAV10",      # missing 'E'
    "SAVE0",     # N < 1
    "SAVE51",    # N > 50
    "SAVED",     # non numeric
    "",
    None,
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee tests ----------
@pytest.mark.parametrize("subtotal, member, expected", [
    (1000.0, False, 0),
    (1200.5, True, 0),
    (999.99, False, 60),
    (200.0, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1e-6, "a"])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal, False)

# ---------- Cart class tests ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_items(self):
        self.cart.add_item("apple", 1.0, 2)
        self.cart.add_item("banana", 0.5, 3)
        items = self.cart.items()
        assert len(items) == 2
        assert any(it["name"] == "apple" and it["quantity"] == 2 for it in items)
        assert any(it["name"] == "banana" and it["quantity"] == 3 for it in items)

    def test_add_existing_item_same_price(self):
        self.cart.add_item("apple", 1.0, 2)
        self.cart.add_item("apple", 1.0, 3)
        assert self.cart.items()[0]["quantity"] == 5

    def test_add_existing_item_different_price_raises(self):
        self.cart.add_item("apple", 1.0, 2)
        with pytest.raises(ValueError):
            self.cart.add_item("apple", 1.5, 1)

    def test_remove_item(self):
        self.cart.add_item("apple", 1.0, 3)
        self.cart.remove_item("apple", 2)
        assert self.cart.items()[0]["quantity"] == 1

    def test_remove_more_than_exists_raises(self):
        self.cart.add_item("apple", 1.0, 1)
        with pytest.raises(ValueError):
            self.cart.remove_item("apple", 2)

    def test_subtotal_and_total_non_member_no_coupon(self):
        self.cart.add_item("apple", 10.0, 5)  # subtotal 50
        assert self.cart.subtotal() == 50
        assert self.cart.total() == 50 + cart.shipping_fee(50)

    def test_total_with_bulk_discount_and_member(self):
        # 10 items triggers 5% discount per item
        self.cart.add_item("apple", 20.0, 10)  # subtotal 200
        expected_sub = 200
        bulk_pct = cart.bulk_discount_percent(10)
        discounted_sub = round(expected_sub * (1 - bulk_pct/100), 2)
        shipping = cart.shipping_fee(discounted_sub, member=True)
        total_expected = discounted_sub + shipping
        assert self.cart.total(member=True) == pytest.approx(total_expected, rel=1e-9)

    def test_total_with_coupon(self):
        self.cart.add_item("apple", 10.0, 2)  # subtotal 20
        coupon_pct = cart.parse_coupon("SAVE10")
        discounted_sub = round(20 * (1 - coupon_pct/100), 2)
        shipping = cart.shipping_fee(discounted_sub)
        total_expected = discounted_sub + shipping
        assert self.cart.total(coupon="SAVE10") == pytest.approx(total_expected, rel=1e-9)
