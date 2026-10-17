import pytest
import cart

def _apply_discount(price: float, percent: int) -> float:
    """Apply discount according to the spec: price reduced by percent%, rounded to 2 decimals."""
    return round(price * (1 - percent / 100.0), 2)

def _bulk_discount_percent(quantity: int) -> int:
    """Bulk discount percent per the spec."""
    if quantity >= 100:
        return 15
    elif quantity >= 50:
        return 10
    elif quantity >= 10:
        return 5
    else:
        return 0

def _shipping_fee(subtotal: float, member: bool = False) -> int:
    """Shipping fee per the spec."""
    if subtotal >= 1000:
        return 0
    return 30 if member else 60

# ---------- apply_discount ----------
@pytest.mark.parametrize("price,percent,expected", [
    (200.0, 15, 170.0),
    (99.999, 10, 90.0),   # 89.9991 rounded to 90.00
    (50.0, 0, 50.0),
    (80.0, 100, 0.0),
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        cart.apply_discount(-5, 10)

@pytest.mark.parametrize("percent", [-1, 101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize("quantity,expected", [
    (5, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -3, 5.7])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    ("  SaVe50   ", 50),
    ("SaVe1", 1),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVEXX",
    "SAVE0",
    "SAVE51",
    "",
    "   ",
    "foo",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize("subtotal,member,expected", [
    (1000.0, False, 0),
    (1500.0, True, 0),
    (999.99, False, 60),
    (500.0, False, 60),
    (500.0, True, 30),
    (0.0, False, 60),
    (0.0, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

def test_shipping_fee_negative_subtotal():
    with pytest.raises(ValueError):
        cart.shipping_fee(-10, False)

# ---------- Cart ----------
class TestCart:
    def test_add_item_basic(self):
        c = cart.Cart()
        c.add_item("Apple", 1.00, 5)
        assert c.items() == {"Apple": 5}

    def test_add_item_increment(self):
        c = cart.Cart()
        c.add_item("Apple", 1.0, 5)
        c.add_item("Apple", 1.0, 2)
        assert c.items() == {"Apple": 7}

    def test_add_item_price_mismatch(self):
        c = cart.Cart()
        c.add_item("Apple", 1.0, 3)
        with pytest.raises(ValueError):
            c.add_item("Apple", 1.5, 2)

    def test_add_item_zero_price_allowed(self):
        c = cart.Cart()
        c.add_item("Freebie", 0.0, 3)
        assert c.items() == {"Freebie": 3}

    def test_add_item_negative_price(self):
        c = cart.Cart()
        with pytest.raises(ValueError):
            c.add_item("BadItem", -1.0, 1)

    @pytest.mark.parametrize("qty", [0, -2])
    def test_add_item_invalid_quantity(self, qty):
        c = cart.Cart()
        with pytest.raises(ValueError):
            c.add_item("Apple", 1.0, qty)

    def test_remove_partial(self):
        c = cart.Cart()
        c.add_item("Apple", 1.0, 7)
        c.remove_item("Apple", 3)
        assert c.items() == {"Apple": 4}

    def test_remove_full_and_deleted(self):
        c = cart.Cart()
        c.add_item("Apple", 1.0, 4)
        c.remove_item("Apple", 4)
        # After full removal, the item should no longer be present
        assert "Apple" not in c.items()

    def test_remove_nonexistent_raises(self):
        c = cart.Cart()
        with pytest.raises(KeyError):
            c.remove_item("NonExistent", 1)

    def test_remove_more_than_existing_deletes(self):
        c = cart.Cart()
        c.add_item("Apple", 1.0, 3)
        c.remove_item("Apple", 10)  # More than existing
        assert "Apple" not in c.items()

    def test_items_immutability(self):
        c = cart.Cart()
        c.add_item("Apple", 1.0, 5)
        items_dict = c.items()
        items_dict["Apple"] = 999   # Mutate returned dict
        items_dict["NewItem"] = 2
        assert c.items() == {"Apple": 5}

    def test_subtotal_single_no_discount(self):
        c = cart.Cart()
        c.add_item("Apple", 1.0, 5)
        assert c.subtotal() == 5.0

    def test_subtotal_with_bulk_discount(self):
        c = cart.Cart()
        c.add_item("Apple", 10.0, 10)  # bulk discount 5%
        expected_line_total = _apply_discount(10.0 * 10, 5)
        assert c.subtotal() == expected_line_total

    def test_subtotal_multiple_items_rounding(self):
        c = cart.Cart()
        c.add_item("A", 3.333, 10)   # bulk discount 5%
        line_a_total = _apply_discount(3.333 * 10, 5)
        c.add_item("B", 1.0, 3)      # no discount
        expected_subtotal = round(line_a_total + (1.0 * 3), 2)
        assert c.subtotal() == expected_subtotal

    def test_subtotal_empty(self):
        assert cart.Cart().subtotal() == 0

    def test_total_empty_cart(self):
        assert cart.Cart().total() == 0

    def test_total_no_coupon_non_member(self):
        c = cart.Cart()
        # Apple: 10*10 with 5% discount =>95
        c.add_item("Apple", 10.0, 10)
        # Banana: 2*3 no discount =>6
        c.add_item("Banana", 2.0, 3)
        subtotal = c.subtotal()
        shipping = _shipping_fee(subtotal, False)
        expected_total = round(subtotal + shipping, 2)
        assert c.total() == expected_total

    def test_total_no_coupon_member(self):
        c = cart.Cart()
        c.add_item("Apple", 10.0, 10)
        c.add_item("Banana", 2.0, 3)
        subtotal = c.subtotal()
        shipping = _shipping_fee(subtotal, True)
        expected_total = round(subtotal + shipping, 2)
        assert c.total(member=True) == expected_total

    def test_total_coupon_over_free_shipping(self):
        c = cart.Cart()
        # Expensive: 200*6 =1200
        c.add_item("Expensive", 200.0, 6)
        subtotal = c.subtotal()
        coupon_percent = cart.parse_coupon("SAVE50")
        discounted_amount = _apply_discount(subtotal, coupon_percent)
        shipping = _shipping_fee(discounted_amount, False)
        expected_total = round(discounted_amount + shipping, 2)
        # The implementation uses original subtotal for shipping,
        # which will produce a lower total. This test should fail if the bug is present.
        assert c.total(coupon="SAVE50") == expected_total

    def test_total_coupon_invalid_raises(self):
        c = cart.Cart()
        with pytest.raises(ValueError):
            c.total(coupon="INVALID")
