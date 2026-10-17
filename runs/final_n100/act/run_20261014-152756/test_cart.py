import pytest
import cart

# ---- apply_discount -------------------------------------------------

def test_apply_discount_basic():
    # Simple case
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (100, 10, 90.0),          # simple percentage
        (123.45, 20, 98.76),      # rounding down
        (123.44, 20, 98.75),      # rounding ties
    ],
)
def test_apply_discount_various(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# Edge cases: price zero, percent zero, percent 100
assert cart.apply_discount(0, 50) == 0.0
assert cart.apply_discount(500, 0) == 500.0
assert cart.apply_discount(500, 100) == 0.0

# Invalid inputs
with pytest.raises(ValueError):
    cart.apply_discount(-10, 20)
with pytest.raises(ValueError):
    cart.apply_discount(100, -5)
with pytest.raises(ValueError):
    cart.apply_discount(100, 105)

# ---- bulk_discount_percent ------------------------------------------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (9, 0),   # below threshold
        (10, 5),  # first tier
        (49, 5),
        (50, 10), # second tier
        (99, 10),
        (100, 15),# third tier
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

with pytest.raises(ValueError):
    cart.bulk_discount_percent(0)
with pytest.raises(ValueError):
    cart.bulk_discount_percent(-5)

# ---- parse_coupon ---------------------------------------------------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        ("  SaVe30  ", 30),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# Invalid coupons
invalid_codes = ["SAVE0", "SAVE51", "SAVEX", "10SAVE", "", "   "]
for c in invalid_codes:
    with pytest.raises(ValueError):
        cart.parse_coupon(c)

# ---- shipping_fee ---------------------------------------------------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (500, False, 60),
        (999.99, False, 60),
        (1000, False, 0),
        (1500, True, 0),
        (300, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

with pytest.raises(ValueError):
    cart.shipping_fee(-10)

# ---- Cart class ------------------------------------------------------
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_empty_cart_total_and_subtotal(self):
        assert self.c.subtotal() == 0.0
        assert self.c.total() == 0.0

    def test_add_item_and_subtotal(self):
        self.c.add_item("apple", 5, quantity=3)
        self.c.add_item("banana", 2, quantity=4)
        # subtotal = 3*5 + 4*2 = 15 + 8 = 23
        assert self.c.subtotal() == 23.0

    def test_remove_item(self):
        self.c.add_item("apple", 5, quantity=5)
        self.c.remove_item("apple", quantity=2)
        # remaining 3 apples
        assert self.c.items()["apple"]['quantity'] == 3

    def test_total_with_coupon_and_member(self):
        self.c.add_item("widget", 100, quantity=1)
        # subtotal 100 -> coupon SAVE10 => 90, shipping 60 (non-member) => 150
        assert self.c.total(coupon="SAVE10") == 150.0
        # member: shipping half
        assert self.c.total(member=True, coupon="SAVE10") == 135.0

    def test_total_without_coupon(self):
        self.c.add_item("gadget", 200, quantity=1)
        # subtotal 200 -> shipping 60 => 260
        assert self.c.total() == 260.0

    def test_total_with_invalid_coupon_raises(self):
        with pytest.raises(ValueError):
            self.c.add_item("item", 10, quantity=1)
            self.c.total(coupon="BAD")

    def test_shipping_free_on_high_subtotal(self):
        self.c.add_item("expensive", 1200, quantity=1)
        assert self.c.total() == 1200.0  # no shipping

# End of test file
