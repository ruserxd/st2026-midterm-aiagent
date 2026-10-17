import pytest
import cart

# ---------- apply_discount ----------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_price_negative(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 110])
def test_apply_discount_percent_out_of_range(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize("quantity,result", [
    (5, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, result):
    assert cart.bulk_discount_percent(quantity) == result

@pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE5 ", 5),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", ["SAVEX", "SAVE0", "SAVE51", "INVALID", "" , "  "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize("subtotal,member,fee", [
    (0, False, 60),
    (500, True, 30),
    (1000, False, 0),
    (1200, True, 0),
])
def test_shipping_fee(subtotal, member, fee):
    assert cart.shipping_fee(subtotal, member) == fee

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart behavior ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_items(self):
        self.cart.add_item("apple", 1.00, 3)
        assert self.cart.items() == {"apple": 3}
        # adding same item increases quantity
        self.cart.add_item("apple", 1.00, 2)
        assert self.cart.items() == {"apple": 5}

    def test_add_same_name_different_price(self):
        self.cart.add_item("banana", 0.50, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 0.60, 2)

    def test_remove_item_partial_and_full(self):
        self.cart.add_item("cherry", 0.30, 4)
        self.cart.remove_item("cherry", 2)
        assert self.cart.items() == {"cherry": 2}
        # removing remaining removes entry
        self.cart.remove_item("cherry", 2)
        assert self.cart.items() == {}

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("durian", 1)

    def test_subtotal_no_discount(self):
        self.cart.add_item("egg", 2.00, 3)  # quantity 3 -> no discount
        assert self.cart.subtotal() == 6.0

    def test_subtotal_with_bulk_discount(self):
        # 12 units => bulk discount 5%
        self.cart.add_item("fig", 1.50, 12)
        expected = round(1.50 * 12 * (1 - 0.05), 2)
        assert self.cart.subtotal() == expected

    def test_total_without_coupon_or_member(self):
        self.cart.add_item("grape", 0.10, 10)  # bulk 5% -> subtotal
        subtotal = self.cart.subtotal()
        total = cart.shipping_fee(subtotal)
        assert round(self.cart.total(), 2) == round(subtotal + total, 2)

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("honey", 20.00, 5)  # no bulk discount
        subtotal = self.cart.subtotal()
        coupon_percent = cart.parse_coupon("SAVE10")
        after_coupon = round(subtotal * (1 - coupon_percent / 100), 2)
        shipping = cart.shipping_fee(after_coupon, member=True)
        expected_total = round(after_coupon + shipping, 2)
        assert self.cart.total(member=True, coupon="SAVE10") == expected_total

    def test_total_empty_cart(self):
        assert self.cart.total() == 0.0

    def test_total_invalid_coupon_raises(self):
        self.cart.add_item("item", 1.00, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")
