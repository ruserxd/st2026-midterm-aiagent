import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- helper functions ----------

def round2(x):
    return round(float(x), 2)

# ---------- tests for individual functions ----------

class TestApplyDiscount:
    def test_basic(self):
        assert apply_discount(200, 15) == 170.0
        assert apply_discount(100, 0) == 100.0
        assert apply_discount(50, 100) == 0.0

    def test_rounding(self):
        # 99% of 33 should be 32.67 rounded to 2 decimals
        assert apply_discount(33, 1) == 32.67

    def test_invalid_price(self):
        with pytest.raises(ValueError):
            apply_discount(-5, 10)

    def test_invalid_percent(self):
        for bad in (-10, 110):
            with pytest.raises(ValueError):
                apply_discount(100, bad)

class TestBulkDiscountPercent:
    @pytest.mark.parametrize(
        "qty,expected",
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
    def test_quantities(self, qty, expected):
        assert bulk_discount_percent(qty) == expected

    def test_invalid_qty_type(self):
        for bad in (0, -5, 3.5, "10"):
            with pytest.raises(ValueError):
                bulk_discount_percent(bad)

class TestParseCoupon:
    @pytest.mark.parametrize(
        "code,expected",
        [
            ("SAVE10", 10),
            ("save10", 10),
            (" SAVE20 ", 20),
            ("SaVe5", 5),
        ],
    )
    def test_valid(self, code, expected):
        assert parse_coupon(code) == expected

    @pytest.mark.parametrize("bad_code", [
        "",
        "save0",
        "save51",
        "foo10",
        " SAVE -5 ",
        123,
    ])
    def test_invalid(self, bad_code):
        with pytest.raises(ValueError):
            parse_coupon(bad_code)

class TestShippingFee:
    @pytest.mark.parametrize(
        "subtotal,f_member,result",
        [
            (0, False, 60),
            (500, True, 30),
            (1000, False, 0),
            (999.99, False, 60),
            (1000, True, 0),
        ],
    )
    def test_cases(self, subtotal, f_member, result):
        assert shipping_fee(subtotal, member=f_member) == result

    def test_negative_subtotal(self):
        with pytest.raises(ValueError):
            shipping_fee(-10)

# ---------- tests for Cart class ----------

class TestCart:
    def test_init_empty(self):
        cart = Cart()
        assert cart.items() == {}
        assert cart.subtotal() == 0
        assert cart.total() == 0

    def test_add_and_remove(self):
        cart = Cart()
        cart.add_item("apple", 2.5, 3)
        assert cart.items() == {"apple": 3}
        # Adding same item with same price increases quantity
        cart.add_item("apple", 2.5, 2)
        assert cart.items() == {"apple": 5}

        # Removing part of quantity
        cart.remove_item("apple", 2)
        assert cart.items() == {"apple": 3}

        # Removing all should delete entry
        cart.remove_item("apple", 3)
        assert cart.items() == {}

    def test_add_duplicate_different_price(self):
        cart = Cart()
        cart.add_item("banana", 1.0, 2)
        with pytest.raises(ValueError):
            cart.add_item("banana", 1.5, 1)

    def test_subtotal_with_bulk_discount(self):
        cart = Cart()
        # 10 units at $1 each => bulk discount 5%
        cart.add_item("itemA", 1.0, 10)
        assert round2(cart.subtotal()) == 9.55

    def test_total_no_coupon_member(self):
        cart = Cart()
        cart.add_item("widget", 200, 6)  # no bulk discount
        # subtotal 1200, shipping free, total 1200
        assert round2(cart.total(member=True)) == 1200.00

    def test_total_with_coupon_and_shipping(self):
        cart = Cart()
        cart.add_item("gadget", 100, 5)  # no bulk discount
        subtotal = 500
        assert cart.subtotal() == subtotal
        total_no_ship = parse_coupon("SAVE10")
        after_coupon = apply_discount(subtotal, 10)
        expected_shipping = shipping_fee(after_coupon, member=False)
        expected_total = round2(after_coupon + expected_shipping)
        assert round2(cart.total(coupon="SAVE10")) == expected_total

    def test_invalid_coupon(self):
        cart = Cart()
        cart.add_item("thing", 50, 1)
        with pytest.raises(ValueError):
            cart.total(coupon="BADCODE")

    def test_empty_cart_no_shipping(self):
        cart = Cart()
        assert cart.total() == 0

# ---------- coverage of edge cases ----------

@pytest.mark.parametrize("name,price,qty", [
    ("a", -1, 1),
    ("b", 10, 0),
])
def test_add_invalid(name, price, qty):
    cart = Cart()
    with pytest.raises(ValueError):
        cart.add_item(name, price, qty)

@pytest.mark.parametrize("name,qty", [
    ("nonexistent", 1),
])
def test_remove_nonexistent(name, qty):
    cart = Cart()
    with pytest.raises(KeyError):
        cart.remove_item(name, qty)
