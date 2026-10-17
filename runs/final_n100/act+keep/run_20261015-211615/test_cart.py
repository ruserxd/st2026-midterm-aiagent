import cart
import pytest

# ----------- apply_discount -----------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price,percent,result", [
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount_edge_cases(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price", [-10, -1, -0.01])
def test_apply_discount_invalid_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 20)

@pytest.mark.parametrize("percent", [ -5, 101, 150])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ----------- bulk_discount_percent -----------------

def test_bulk_discount_percent_values():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@pytest.mark.parametrize("quantity", [0, -1, -5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ----------- parse_coupon -----------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon("  SaVe30  ") == 30

@pytest.mark.parametrize("code", ["",
                                   "SAVExx",
                                   "saver10",
                                   "SAVE0",
                                   "SAVE51",
                                   "100"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ----------- shipping_fee -----------------

def test_shipping_fee_standard():
    assert cart.shipping_fee(999) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(5000) == 0

@pytest.mark.parametrize("subtotal,member,expected", [
    (900, True, 30),
    (900, False, 60),
])
def test_shipping_fee_membership(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

@pytest.mark.parametrize("subtotal", [-1, -0.01])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ----------- Cart class -----------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_items(self):
        self.cart.add_item("apple", 100, quantity=2)
        self.cart.add_item("banana", 50)
        items = self.cart.items()
        assert len(items) == 2
        names = {i["name"] for i in items}
        assert names == {"apple", "banana"}

    def test_remove_and_items(self):
        self.cart.add_item("pear", 200, quantity=3)
        self.cart.remove_item("pear", quantity=1)
        remaining = [i for i in self.cart.items() if i["name"] == "pear"]
        assert remaining[0]["quantity"] == 2
        # remove more than existing should delete item
        self.cart.remove_item("pear", quantity=5)
        assert all(i["name"] != "pear" for i in self.cart.items())

    def test_subtotal(self):
        self.cart.add_item("x", 100, quantity=3)
        self.cart.add_item("y", 50, quantity=2)
        assert self.cart.subtotal() == 100*3 + 50*2

    def test_total_no_coupon_member_false(self):
        self.cart.add_item("item", 200, quantity=1)
        expected = 200 + 60
        assert self.cart.total(member=False) == expected

    def test_total_with_coupon_and_shipping(self):
        self.cart.add_item("expensive", 1200, quantity=1)
        total = self.cart.total(coupon="SAVE10")
        assert total == round(1200 * (1-0.10),2)

    def test_total_empty_cart(self):
        assert self.cart.total() == 0

    def test_total_invalid_coupon_raises(self):
        self.cart.add_item("thing", 100, quantity=1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")
