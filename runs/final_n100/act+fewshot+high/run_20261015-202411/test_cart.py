import pytest
import cart

# Tests for apply_discount
def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0
    assert cart.apply_discount(123.46, 10) == 111.11

@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# Tests for bulk_discount_percent
def test_bulk_discount_percent_boundaries():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

@pytest.mark.parametrize("quantity", [0, -1, 3.5, "10"])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# Tests for parse_coupon
def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save10") == 10
    assert cart.parse_coupon(" SAVE50 ") == 50
    assert cart.parse_coupon("sAVe1") == 1

@pytest.mark.parametrize("code", [
    "SAVE",            # missing digits
    "SAVExx",          # non-digit suffix
    "save0",           # percent 0 out of range
    "save51",          # percent >50
    None,               # not a string
    "",                # empty string
    123,                # not a string
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Tests for shipping_fee
def test_shipping_fee_basic():
    assert cart.shipping_fee(999, False) == 60
    assert cart.shipping_fee(999, True) == 30
    assert cart.shipping_fee(1000, False) == 0
    assert cart.shipping_fee(1000, True) == 0
    assert cart.shipping_fee(500, False) == 60
    assert cart.shipping_fee(500, True) == 30

@pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Tests for Cart
class TestCart:
    def test_add_item_basic(self):
        c = cart.Cart()
        c.add_item("apple", 1.5, 3)
        assert c.items() == {"apple": 3}
        # Adding same item increases quantity
        c.add_item("apple", 1.5, 2)
        assert c.items() == {"apple": 5}

    def test_add_item_price_mismatch(self):
        c = cart.Cart()
        c.add_item("banana", 2.0, 1)
        with pytest.raises(ValueError):
            c.add_item("banana", 3.0, 1)

    @pytest.mark.parametrize("unit_price", [-1.0, -10])
    def test_add_item_negative_unit_price(self, unit_price):
        c = cart.Cart()
        with pytest.raises(ValueError):
            c.add_item("pear", unit_price, 1)

    @pytest.mark.parametrize("quantity", [0, -5, 2.3, "a"])
    def test_add_item_invalid_quantity(self, quantity):
        c = cart.Cart()
        with pytest.raises(ValueError):
            c.add_item("orange", 1.0, quantity)

    def test_remove_item_partial(self):
        c = cart.Cart()
        c.add_item("apple", 1.0, 3)
        c.remove_item("apple", 2)
        assert c.items() == {"apple": 1}

    def test_remove_item_delete_when_zero(self):
        c = cart.Cart()
        c.add_item("orange", 1.5, 2)
        c.remove_item("orange", 2)
        # Expected: item removed entirely
        assert "orange" not in c.items()

    def test_remove_more_than_quantity(self):
        c = cart.Cart()
        c.add_item("pear", 2.0, 3)
        c.remove_item("pear", 5)
        assert "pear" not in c.items()

    def test_remove_nonexistent_item(self):
        c = cart.Cart()
        with pytest.raises(KeyError):
            c.remove_item("nonexistent")

    def test_items_copy_is_new_dict(self):
        c = cart.Cart()
        c.add_item("pear", 1.0, 2)
        d = c.items()
        d["pear"] = 10
        assert c.items()["pear"] == 2
        e = c.items()
        assert d is not e

    def test_subtotal_basic(self):
        c = cart.Cart()
        c.add_item("A", 10, 3)   # 30 no discount
        c.add_item("B", 7, 15)   # quantity 15 -> bulk discount 5% => 105*0.95=99.75
        c.add_item("C", 1, 2)    # 2 no discount
        expected = round(30 + 99.75 + 2, 2)
        assert c.subtotal() == expected

    def test_subtotal_empty(self):
        c = cart.Cart()
        assert c.subtotal() == 0

    def test_total_no_coupon_non_member(self):
        c = cart.Cart()
        c.add_item("A", 10, 3)
        c.add_item("B", 7, 15)
        c.add_item("C", 1, 2)
        subtotal = round(30 + 99.75 + 2, 2)
        shipping = cart.shipping_fee(subtotal, False)
        expected_total = round(subtotal + shipping, 2)
        assert c.total(member=False) == expected_total

    def test_total_with_coupon_non_member(self):
        c = cart.Cart()
        c.add_item("A", 10, 3)
        c.add_item("B", 7, 15)
        c.add_item("C", 1, 2)
        subtotal = round(30 + 99.75 + 2, 2)
        discounted = cart.apply_discount(subtotal, cart.parse_coupon("SAVE10"))
        shipping = cart.shipping_fee(discounted, False)
        expected_total = round(discounted + shipping, 2)
        assert c.total(member=False, coupon="SAVE10") == expected_total

    def test_total_with_coupon_member(self):
        c = cart.Cart()
        c.add_item("A", 10, 3)
        c.add_item("B", 7, 15)
        c.add_item("C", 1, 2)
        subtotal = round(30 + 99.75 + 2, 2)
        discounted = cart.apply_discount(subtotal, cart.parse_coupon("SAVE10"))
        shipping = cart.shipping_fee(discounted, True)
        expected_total = round(discounted + shipping, 2)
        assert c.total(member=True, coupon="SAVE10") == expected_total

    def test_total_with_coupon_crossing_threshold(self):
        # Build a cart with subtotal >= 1000
        c = cart.Cart()
        for i in range(11):
            c.add_item(f"item{i}", 100, 1)
        subtotal_before = c.subtotal()
        assert subtotal_before >= 1000
        discounted = cart.apply_discount(subtotal_before, cart.parse_coupon("SAVE20"))
        shipping_expected = cart.shipping_fee(discounted, False)   # should be 60
        expected_total = round(discounted + shipping_expected, 2)
        actual_total = c.total(member=False, coupon="SAVE20")
        assert actual_total == expected_total, f"Expected {expected_total} but got {actual_total}"

    def test_total_invalid_coupon(self):
        c = cart.Cart()
        c.add_item("A", 1.0, 1)
        with pytest.raises(ValueError):
            c.total(coupon="INVALID")

    def test_total_empty_cart(self):
        c = cart.Cart()
        assert c.total() == 0
        assert c.total(member=True) == 0
        assert c.total(coupon="SAVE10") == 0
