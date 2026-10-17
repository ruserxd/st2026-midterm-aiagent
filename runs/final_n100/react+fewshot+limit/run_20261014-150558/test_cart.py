import pytest
import cart

# ---------- apply_discount -------------------------------------------------
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),          # example from spec
        (100, 0, 100.0),           # no discount
        (50, 100, 0.0),            # full discount
        (99.99, 25, round(99.99 * 0.75, 2)),
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price, percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ------------------------------------------
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (1, 0),
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 2.5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ---------------------------------------------------
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        (" SAVE30 ", 30),
        ("SaVe50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVEX",          # not integer
    "SAVE0",          # below range
    "SAVE51",         # above range
    "ABCD10",         # wrong prefix
    "SAVE-5",         # negative
    "",               # empty
    "   ",           # whitespace only
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------------------------------------------------
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, 60),
        (999.99, False, 60),
        (1000, False, 0),
        (2000, True, 0),
        (150, True, 30),
        (50, False, 60),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class -----------------------------------------------------
class TestCart:
    def test_empty_cart(self):
        c = cart.Cart()
        assert c.items() == {}
        assert c.subtotal() == 0.0
        assert c.total() == 0.0

    def test_add_and_remove(self):
        c = cart.Cart()
        c.add_item("apple", 100, 2)
        # bulk discount for 2 items: 0%
        assert c.items() == {"apple": 2}
        assert c.subtotal() == 200.0
        # add same item with same price increases quantity
        c.add_item("apple", 100, 3)
        assert c.items() == {"apple": 5}
        # subtotal now 500, bulk discount for 5 items: 0%
        assert c.subtotal() == 500.0
        # remove some
        c.remove_item("apple", 2)
        assert c.items() == {"apple": 3}
        assert c.subtotal() == 300.0
        # removing more than present removes item completely
        c.remove_item("apple", 5)
        assert c.items() == {}

    def test_add_same_name_different_price(self):
        c = cart.Cart()
        c.add_item("orange", 50, 1)
        with pytest.raises(ValueError):
            c.add_item("orange", 60, 1)  # price mismatch

    def test_invalid_add_remove_params(self):
        c = cart.Cart()
        with pytest.raises(ValueError):
            c.add_item("pear", -10, 1)
        with pytest.raises(ValueError):
            c.add_item("pear", 10, 0)
        with pytest.raises(KeyError):
            c.remove_item("nonexistent", 1)

    def test_total_with_coupon_and_shipping(self):
        # Setup: two items, one triggers bulk discount
        c = cart.Cart()
        c.add_item("itemA", 100, 10)   # bulk discount 5%
        c.add_item("itemB", 200, 1)
        subtotal_expected = round(100 * 10 * 0.95 + 200 * 1, 2)
        assert c.subtotal() == subtotal_expected

        # Apply coupon SAVE20 (20% off after bulk discount)
        total_with_coupon = cart.total(c.subtotal(), coupon="SAVE20")
        # Expected: apply 20% to subtotal, then add shipping if any
        discounted = round(subtotal_expected * 0.80, 2)
        shipping = cart.shipping_fee(discounted)
        expected_total = round(discounted + shipping, 2)
        assert total_with_coupon == expected_total

    def test_total_without_items(self):
        c = cart.Cart()
        assert c.total() == 0.0

    def test_total_member_shipping_free(self):
        c = cart.Cart()
        c.add_item("big", 500, 3)   # subtotal 1500 > 1000 => free shipping
        total = c.total(member=True)
        assert total == round(1500.0, 2)  # no discount applied by default

    def test_total_with_invalid_coupon(self):
        c = cart.Cart()
        c.add_item("item", 50, 1)
        with pytest.raises(ValueError):
            c.total(coupon="BAD")
