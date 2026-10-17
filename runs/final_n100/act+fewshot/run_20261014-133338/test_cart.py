import pytest
import cart

# ---------- apply_discount ---------------------------------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# error cases
@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 20)

@pytest.mark.parametrize("percent", [-5, 150])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent ---------------------------
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 2.5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon -------------------------------------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save25", 25),
    ("  SaVe5  ", 5),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "SAVExx", "ABCD10", "" ])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee -------------------------------------
@pytest.mark.parametrize("subtotal,member,result", [
    (1000, False, 0),
    (999.99, False, 60),
    (200, True, 30),
])
def test_shipping_fee(subtotal, member, result):
    assert cart.shipping_fee(subtotal, member) == result

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart functionality ---------------------------------
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_add_and_items(self):
        self.c.add_item("apple", 1.0, 3)
        self.c.add_item("banana", 0.5, 2)
        assert self.c.items() == {"apple": 3, "banana": 2}

    def test_add_existing_increase_quantity_and_price_match(self):
        self.c.add_item("orange", 1.5, 4)
        self.c.add_item("orange", 1.5, 1)
        assert self.c.items() == {"orange": 5}

    def test_add_existing_price_mismatch_raises(self):
        self.c.add_item("grape", 2.0, 1)
        with pytest.raises(ValueError):
            self.c.add_item("grape", 3.0, 2)

    def test_remove_item_and_deletion_when_zero(self):
        self.c.add_item("kiwi", 0.8, 5)
        self.c.remove_item("kiwi", 3)
        assert self.c.items() == {"kiwi": 2}
        self.c.remove_item("kiwi", 2)
        assert self.c.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.c.remove_item("pear", 1)

    def test_subtotal_bulk_discount(self):
        # 10 apples at $2 each => bulk discount 5% -> 20*0.95=19.0
        self.c.add_item("apple", 2.0, 10)
        assert self.c.subtotal() == 19.0

    def test_total_without_coupon(self):
        self.c.add_item("book", 30.0, 1)
        # subtotal 30 -> shipping 60 (non-member) => total 90
        assert self.c.total(member=False) == 90.0

    def test_total_with_member_and_coupon(self):
        self.c.add_item("pen", 5.0, 50)  # bulk discount 10% -> subtotal 225
        # coupon SAVE10 -> reduce by 10% => 202.5
        # shipping member half of 60 =30 (subtotal <1000) => total 232.5
        assert self.c.total(member=True, coupon="SAVE10") == 232.5

    def test_total_empty_cart(self):
        assert self.c.total() == 0
