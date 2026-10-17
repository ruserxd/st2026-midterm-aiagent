import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------------------------------------------------------------------------
# apply_discount
# ---------------------------------------------------------------------------

def test_apply_discount_normal():
    assert apply_discount(200, 15) == 170.0

@pytest.mark.parametrize(
    "price,percent,result",
    [
        (100, 0, 100.00),   # no discount
        (100, 100, 0.00),   # full discount
        (99.999, 10, 90.00),# rounding
    ],
)
def test_apply_discount_edges(price, percent, result):
    assert apply_discount(price, percent) == result

@pytest.mark.parametrize(
    "price,percent",
    [(-1, 10), (50, -5), (50, 105)],
)
def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------------------------------------------------------------------------
# bulk_discount_percent
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "qty,expected",
    [
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(qty, expected):
    assert bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -5, 3.2])
def test_bulk_discount_percent_invalid(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)

# ---------------------------------------------------------------------------
# parse_coupon
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        (" save20 ", 20),
        ("sAvE50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVExx", "10SAVE", "SAVEXX", " ", "SAVE51"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------------------------------------------------------------------------
# shipping_fee
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (500, True, 30),
        (999.99, False, 60),
        (1000, False, 0),
        (1500, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------------------------------------------------------------------------
# Cart
# ---------------------------------------------------------------------------
class TestCart:
    def test_add_item_new(self):
        cart = Cart()
        cart.add_item("apple", 1.0, 3)
        assert cart.items() == {"apple": 3}

    def test_add_item_existing_same_price(self):
        cart = Cart()
        cart.add_item("banana", 0.5, 2)
        cart.add_item("banana", 0.5, 4)
        assert cart.items() == {"banana": 6}

    def test_add_item_existing_different_price(self):
        cart = Cart()
        cart.add_item("orange", 1.5, 1)
        with pytest.raises(ValueError):
            cart.add_item("orange", 2.0, 1)

    def test_remove_item_partial_and_zero(self):
        cart = Cart()
        cart.add_item("pear", 2.0, 3)
        cart.remove_item("pear", 1)   # left 2
        assert cart.items() == {"pear": 2}
        cart.remove_item("pear", 2)   # removed completely
        assert cart.items() == {}

    def test_remove_nonexistent_raises(self):
        cart = Cart()
        with pytest.raises(KeyError):
            cart.remove_item("mango", 1)

    def test_subtotal_no_discount(self):
        cart = Cart()
        cart.add_item("item", 10.0, 4)   # qty < 10 => no discount
        assert cart.subtotal() == 40.00

    def test_subtotal_with_bulk_discount(self):
        cart = Cart()
        cart.add_item("widget", 5.0, 12)  # qty >= 10 -> 5% off per unit
        expected = round(5.0 * 12 * (1 - 0.05), 2)
        assert cart.subtotal() == expected

    def test_total_no_coupon_member(self):
        cart = Cart()
        cart.add_item("gadget", 100.0, 10)  # qty=10 => 5% bulk discount
        subtotal = cart.subtotal()          # calculated above
        total_expected = round(subtotal + shipping_fee(subtotal), 2)
        assert cart.total(member=False) == total_expected

    def test_total_with_coupon_and_member(self):
        cart = Cart()
        cart.add_item("tool", 200.0, 5)     # no bulk discount
        subtotal = cart.subtotal()          # 1000.00
        coupon_percent = parse_coupon("SAVE10")
        discounted = round(subtotal * (1 - coupon_percent / 100), 2)
        shipping = shipping_fee(discounted, member=True)
        total_expected = round(discounted + shipping, 2)
        assert cart.total(member=True, coupon="SAVE10") == total_expected

    def test_total_invalid_coupon_raises(self):
        cart = Cart()
        cart.add_item("thing", 50.0, 1)
        with pytest.raises(ValueError):
            cart.total(coupon="BADCODE")

    def test_empty_cart_zero_cost(self):
        cart = Cart()
        assert cart.total() == 0.00
        # shipping should not be applied for empty cart (spec says no shipping)
        assert shipping_fee(0) == 60  # but total uses subtotal 0, shipping added? spec: no shipping if empty
        # In our implementation shipping is only added if subtotal>0? We test that total returns 0.

# ---------------------------------------------------------------------------
# End of tests
