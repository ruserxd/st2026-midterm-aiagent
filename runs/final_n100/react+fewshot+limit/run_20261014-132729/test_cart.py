import pytest
import cart

# ---------- apply_discount ---------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price,percent", [(-1,10),(100,-5),(100,105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ---------

def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

@pytest.mark.parametrize("quantity", [0,-1,2.5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ---------

def test_parse_coupon_valid():
    assert cart.parse_coupon('SAVE10') == 10
    assert cart.parse_coupon(' save25 ') == 25
    assert cart.parse_coupon('SaVe50') == 50

@pytest.mark.parametrize("code", ["SAVEE", "SAVE0", "SAVE51", "XX10", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ---------

def test_shipping_fee():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(500, member=True) == 30

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart functionality ---------
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_add_and_items(self):
        self.c.add_item('apple', 1.0, 3)
        assert self.c.items() == {'apple':3}
        # add same item increases quantity
        self.c.add_item('apple', 1.0, 2)
        assert self.c.items() == {'apple':5}

    def test_add_invalid(self):
        with pytest.raises(ValueError):
            self.c.add_item('banana', -1, 1)
        with pytest.raises(ValueError):
            self.c.add_item('banana', 1, 0)

    def test_remove(self):
        self.c.add_item('orange', 2.5, 4)
        self.c.remove_item('orange', 2)
        assert self.c.items() == {'orange':2}
        # removing more than present removes the item
        self.c.remove_item('orange', 3)
        assert self.c.items() == {}

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.c.remove_item('pear', 1)

    def test_subtotal_no_discount(self):
        self.c.add_item('toy', 10.0, 2)  # qty<10 no bulk
        assert self.c.subtotal() == 20.00

    def test_subtotal_with_bulk(self):
        self.c.add_item('widget', 5.0, 12)  # qty>=10 gives 5% discount per item
        expected = 5.0 * 12 * (1-0.05)
        assert self.c.subtotal() == round(expected,2)

    def test_total_with_coupon_and_shipping(self):
        self.c.add_item('book', 30.0, 3)  # subtotal 90
        total = self.c.total(coupon='SAVE10')
        # subtotal after coupon: 81; shipping fee 60 -> 141
        assert total == round(81+60,2)

    def test_total_empty_cart(self):
        assert self.c.total() == 0.00

    def test_total_invalid_coupon(self):
        with pytest.raises(ValueError):
            self.c.total(coupon='BADCODE')
