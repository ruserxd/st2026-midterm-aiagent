import pytest
import cart

# ---------- apply_discount ----------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),           # example
    (100, 0, 100.0),            # no discount
    (50, 100, 0.0),             # full discount
])
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# invalid price <0
@pytest.mark.parametrize("price,percent", [(-10, 10), (-1, 0)])
def test_apply_discount_invalid_price(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# invalid percent out of range
@pytest.mark.parametrize("price,percent", [(100, -5), (100, 150)])
def test_apply_discount_invalid_percent(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize("qty,expected", [
    (9, 0),   # less than 10
    (10, 5),  # exactly 10
    (49, 5),  # between 10 and 50
    (50, 10), # exactly 50
    (99, 10), # just below 100
    (100, 15),# exactly 100
    (150, 15),# above 100
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

# invalid quantity non-positive or not int
@pytest.mark.parametrize("qty", [0, -5, 3.2, "10"])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- parse_coupon ----------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save25", 25),
    (" SAVE5 ", 5),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# invalid coupon patterns or out-of-range
@pytest.mark.parametrize("code", [
    "SAV10",   # missing 'E'
    "SAVE0",   # N<1
    "SAVE51",  # N>50
    "XYZ",     # unrelated
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize("subtotal,member,result", [
    (0, False, 60),
    (999.99, True, 30),
    (1000, False, 0),
])
def test_shipping_fee(subtotal, member, result):
    assert cart.shipping_fee(subtotal, member) == result

# invalid subtotal negative
@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ----------
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_initially_empty(self):
        assert self.c.items() == {}
        assert self.c.subtotal() == 0.0
        assert self.c.total() == 0.0

    # add_item tests
    def test_add_new_item(self):
        self.c.add_item("apple", 1.00, 3)
        assert self.c.items() == {"apple": 3}
        # subtotal with bulk discount: qty=3 => 0% => 3.00
        assert self.c.subtotal() == 3.00

    def test_add_existing_same_price(self):
        self.c.add_item("banana", 2.00, 5)
        self.c.add_item("banana", 2.00, 4)
        assert self.c.items() == {"banana": 9}
        # qty=9 => 0% discount
        assert self.c.subtotal() == 18.00

    def test_add_existing_different_price(self):
        self.c.add_item("orange", 1.50, 2)
        with pytest.raises(ValueError):
            self.c.add_item("orange", 2.00, 1)

    # remove_item tests
    def test_remove_some_quantity(self):
        self.c.add_item("kiwi", 3.00, 4)
        self.c.remove_item("kiwi", 2)
        assert self.c.items() == {"kiwi": 2}

    def test_remove_more_than_present_removes(self):
        self.c.add_item("mango", 5.00, 3)
        self.c.remove_item("mango", 5)  # remove all and more
        assert self.c.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.c.remove_item("pineapple", 1)

    # subtotal rounding and bulk discount per item
    def test_subtotal_multiple_items_with_discount(self):
        # apple qty=10 => 5% discount
        self.c.add_item("apple", 2.00, 10)  # base 20 -> 19.0
        # banana qty=50 => 10% discount
        self.c.add_item("banana", 1.00, 50) # base 50 -> 45.0
        assert pytest.approx(self.c.subtotal(), rel=1e-9) == 64.0

    # total calculation with coupon and shipping
    def test_total_with_coupon_and_member_shipping(self):
        self.c.add_item("widget", 100.00, 5)  # qty<10 => no bulk discount: 500
        # subtotal 500
        # apply SAVE20 -> 400
        total = self.c.total(member=True, coupon="SAVE20")
        # shipping on discounted amount 400 > 1000? No, so fee 30 (member)
        assert pytest.approx(total, rel=1e-9) == 430.00

    def test_total_free_shipping(self):
        self.c.add_item("gadget", 300.00, 4)  # subtotal 1200
        total = self.c.total()
        # no coupon, shipping free
        assert pytest.approx(total, rel=1e-9) == 1200.00

    def test_total_invalid_coupon(self):
        self.c.add_item("foo", 10.00, 1)
        with pytest.raises(ValueError):
            self.c.total(coupon="INVALID")

    # total on empty cart returns 0
    def test_total_empty_cart(self):
        assert self.c.total() == 0.0
