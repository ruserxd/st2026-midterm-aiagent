import pytest
import cart

# ---------- apply_discount tests ----------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 10) == 90.0
    assert cart.apply_discount(99.999, 20) == round(99.999 * 0.8, 2)

@pytest.mark.parametrize("price,percent", [(-1, 10), (50, -5), (30, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent tests ----------

def test_bulk_discount_brackets():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@pytest.mark.parametrize("qty", [0, -5, 2.5])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- parse_coupon tests ----------

def test_parse_coupon_valid():
    for code in ["SAVE10", "save20", "  SaVe50 "]:
        # compute expected percent from code after strip and casefold
        expected = int(code.strip().upper()[4:])
        assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVEXY", "SAVE0", "SAVE51", "DISCOUNT10", "", 123, None])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee tests ----------

def test_shipping_fee_non_member():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(5000) == 0

def test_shipping_fee_membership():
    assert cart.shipping_fee(0, member=True) == 30
    assert cart.shipping_fee(999.99, member=True) == 30
    assert cart.shipping_fee(1000, member=True) == 0

@pytest.mark.parametrize("subtotal", [-1, -5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class tests ----------
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_empty_cart_totals(self):
        assert self.c.subtotal() == 0
        assert self.c.total() == 0

    def test_add_and_remove_items(self):
        self.c.add_item("apple", 2.0, quantity=5)
        self.c.add_item("banana", 1.0, quantity=10)
        items = {i['name']: i for i in self.c.items()}
        assert items["apple"] == {'name': 'apple', 'unit_price': 2.0, 'quantity': 5}
        assert items["banana"] == {'name': 'banana', 'unit_price': 1.0, 'quantity': 10}

        self.c.remove_item("apple", quantity=3)
        items = {i['name']: i for i in self.c.items()}
        assert items["apple"]["quantity"] == 2

    def test_subtotal_with_bulk_discount(self):
        # 12 apples at $10 each => bulk discount 5%
        self.c.add_item("apple", 10.0, quantity=12)
        expected = round(10.0 * 12 * (1 - 0.05), 2)
        assert self.c.subtotal() == expected

    def test_total_with_coupon_and_shipping(self):
        # 5 items worth $200 each => no bulk discount, subtotal 1000
        self.c.add_item("widget", 200.0, quantity=5)
        # coupon SAVE10 reduces by 10%
        total = self.c.total(coupon="SAVE10")
        # subtotal after coupon: 900; shipping free
        assert total == round(900, 2)

    def test_total_member_shipping(self):
        self.c.add_item("item", 500.0, quantity=1)  # subtotal 500
        total = self.c.total(member=True)
        # no coupon: 500 + shipping 30 => 530
        assert total == round(530, 2)

    def test_total_invalid_coupon(self):
        self.c.add_item("item", 50.0, quantity=1)
        with pytest.raises(ValueError):
            self.c.total(coupon="BADCODE")
