import pytest
import cart

# ---------- apply_discount -----------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent -----------
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 2.5, "10"])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon -----------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save5", 5),
    ("  SaVe50  ", 50),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "DISCOUNT10", "", "SAVE-5", "SAVEabc"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee -----------
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (500, True, 30),
    (1000, False, 0),
    (1500, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class tests -----------
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_initial_state(self):
        assert self.c.items() == {}
        assert self.c.subtotal() == 0.0
        assert self.c.total() == 0.0

    def test_add_item_new_and_existing(self):
        self.c.add_item("apple", 1.00, 3)
        assert self.c.items() == {"apple": 3}
        # adding same item with same price increases quantity
        self.c.add_item("apple", 1.00, 2)
        assert self.c.items() == {"apple": 5}
        # attempting to add same name with different price raises ValueError
        with pytest.raises(ValueError):
            self.c.add_item("apple", 1.20, 1)

    def test_remove_item(self):
        self.c.add_item("banana", 0.50, 4)
        self.c.remove_item("banana", 2)
        assert self.c.items() == {"banana": 2}
        # removing more than remaining removes item entirely
        self.c.remove_item("banana", 5)
        assert "banana" not in self.c.items()
        # removing non-existent key raises KeyError
        with pytest.raises(KeyError):
            self.c.remove_item("orange", 1)

    def test_subtotal_with_bulk_discount(self):
        # 10 units -> bulk discount 5%
        self.c.add_item("widget", 20.00, 10)  # subtotal before discount 200
        expected = round(200 * (1 - 0.05), 2)
        assert self.c.subtotal() == expected
        # 50 units -> 10% discount
        self.c.remove_item("widget", 10)
        self.c.add_item("gadget", 5.00, 50)   # subtotal before discount 250
        expected = round(250 * (1 - 0.10), 2)
        assert self.c.subtotal() == expected

    def test_total_without_coupon_and_member(self):
        self.c.add_item("thing", 100.00, 1)
        # subtotal 100, no discount, shipping 60 => total 160
        assert self.c.total() == round(100 + 60, 2)

    def test_total_with_coupon_and_member(self):
        self.c.add_item("item", 200.00, 1)
        # subtotal 200, coupon SAVE10 -> 180, shipping fee for member is 30 => total 210
        assert self.c.total(member=True, coupon="SAVE10") == round(180 + 30, 2)

    def test_total_invalid_coupon(self):
        self.c.add_item("item", 50.00, 1)
        with pytest.raises(ValueError):
            self.c.total(coupon="INVALID")

    def test_total_empty_cart_no_shipping(self):
        assert cart.Cart().total() == 0.0
