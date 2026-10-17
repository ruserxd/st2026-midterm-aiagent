import pytest
import cart

# ---------- apply_discount --------------------------------------------------
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),   # example from spec
        (100, 0, 100.0),    # no discount
        (50, 100, 0.0),     # full discount
    ],
)
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# invalid price and percent should raise ValueError
@pytest.mark.parametrize(
    "price,percent",
    [(-1, 10), (10, -5), (10, 105)],
)
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent --------------------------------------------
@pytest.mark.parametrize(
    "quantity,percent",
    [
        (5, 0),      # below threshold
        (10, 5),     # exactly at 10
        (50, 10),    # exactly at 50
        (100, 15),   # exactly at 100
        (200, 15),   # above maximum
    ],
)
def test_bulk_discount_percent(quantity, percent):
    assert cart.bulk_discount_percent(quantity) == percent

@pytest.mark.parametrize(
    "quantity",
    [0, -1, 3.5],
)
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon -----------------------------------------------------
@pytest.mark.parametrize(
    "code,percent",
    [
        ("SAVE10", 10),
        (" save25 ", 25),
        ("SaVe50", 50),   # max allowed
    ],
)
def test_parse_coupon_valid(code, percent):
    assert cart.parse_coupon(code) == percent

@pytest.mark.parametrize(
    "code",
    [
        "SAVE0",          # below min
        "SAVE51",         # above max
        "SAV10",          # missing SAVE prefix
        "XYZ10",          # wrong prefix
        "SAVE-5",         # negative number
        "   ",           # only whitespace
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee -----------------------------------------------------
@pytest.mark.parametrize(
    "subtotal,member,fee",
    [
        (0, False, 60),   # below free threshold
        (999.99, True, 30),
        (1000, False, 0),   # free shipping
        (1500, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, fee):
    assert cart.shipping_fee(subtotal, member) == fee

@pytest.mark.parametrize(
    "subtotal",
    [-1, -10],
)
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class -------------------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_items(self):
        self.cart.add_item("apple", 1.0, 3)
        assert self.cart.items() == {"apple": (1.0, 3)}
        # adding same item increases quantity and must match unit price
        self.cart.add_item("apple", 1.0, 2)
        assert self.cart.items()["apple"] == (1.0, 5)
        with pytest.raises(ValueError):
            # different unit price for existing item
            self.cart.add_item("apple", 1.5, 1)

    def test_add_invalid(self):
        with pytest.raises(ValueError):
            self.cart.add_item("banana", -1.0, 2)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 1.0, 0)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 1.0, 1.5)

    def test_remove(self):
        self.cart.add_item("orange", 2.0, 4)
        # remove less than quantity
        self.cart.remove_item("orange", 2)
        assert self.cart.items()["orange"] == (2.0, 2)
        # remove remaining and item disappears
        self.cart.remove_item("orange", 2)
        assert "orange" not in self.cart.items()
        # removing more than exists should leave empty
        with pytest.raises(KeyError):
            self.cart.remove_item("orange", 1)

    def test_subtotal_and_total(self):
        self.cart.add_item("bread", 3.0, 2)   # subtotal 6.0
        self.cart.add_item("milk", 5.0, 1)    # subtotal 11.0
        assert self.cart.subtotal() == 11.0
        # total without discount or membership
        assert self.cart.total() == 11.0 + cart.shipping_fee(11.0)
        # with member fee half
        assert self.cart.total(member=True) == 11.0 + cart.shipping_fee(11.0, member=True)
        # apply bulk discount: quantity of bread is 2 (<10), so none
        # add more breads to trigger bulk discount
        self.cart.add_item("bread", 3.0, 9)   # total bread qty = 11 -> 5% discount on its part
        assert cart.bulk_discount_percent(11) == 5
        subtotal_with_bread = 3.0*11 + 5.0
        expected_total = subtotal_with_bread * (1-0.05)
        # coupon 'SAVE20'
        assert self.cart.total(coupon="SAVE20") == pytest.approx(expected_total + cart.shipping_fee(subtotal_with_bread))
    
    def test_total_coupon_invalid(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALIDCODE")
