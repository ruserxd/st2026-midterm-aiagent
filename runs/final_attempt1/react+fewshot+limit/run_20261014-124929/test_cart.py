import pytest
import cart

# ---------- apply_discount -------------------------------------------
@pytest.mark.parametrize("price,percent,result", [
    (200.0, 15, 170.0),
    (100.0, 0, 100.0),
    (50.0, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [(-1, 10), (10, -5), (10, 105)])
def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent -------------------------------------
@pytest.mark.parametrize("qty,expected", [
    (9, 0),
    (10, 5),
    (50, 10),
    (100, 15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -1, 3.5])
def test_bulk_discount_invalid_inputs(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- parse_coupon ----------------------------------------------
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    ("save20 ", 20),
    (" SAVE50", 50),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", ["SAV10", "SAVE0", "SAVE51", "foo", "SAVE-5", " SAVE101 "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------------------------------------------
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (500, True, 30),
    (1000, False, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class -------------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initial_state(self):
        assert self.cart.items() == []
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    def test_add_item_and_subtotal(self):
        self.cart.add_item("apple", unit_price=100, quantity=2)
        # subtotal should be 200
        assert self.cart.subtotal() == 200.0
        # items list contains the item
        assert self.cart.items() == [("apple", 100, 2)]

    def test_remove_item_partial(self):
        self.cart.add_item("banana", unit_price=50, quantity=5)
        self.cart.remove_item("banana", quantity=3)
        # remaining quantity should be 2
        assert self.cart.items() == [("banana", 50, 2)]

    def test_remove_item_full(self):
        self.cart.add_item("orange", unit_price=80, quantity=1)
        self.cart.remove_item("orange")  # default qty 1
        assert self.cart.items() == []

    def test_total_with_member_and_coupon(self):
        # add items to exceed $1000 subtotal for shipping free
        self.cart.add_item("widget", unit_price=300, quantity=4)  # 1200 subtotal
        # member=True gives half shipping but free anyway
        total = self.cart.total(member=True, coupon="SAVE20")
        # calculate expected: subtotal 1200, no bulk discount, 20% coupon => 960
        assert total == 960.0

    def test_total_bulk_discount(self):
        # add many units to trigger bulk discount of 5%
        self.cart.add_item("gadget", unit_price=10, quantity=15)  # subtotal 150
        # no coupon, member=False
        total = self.cart.total()
        # bulk discount percent for 15 is 5% -> apply_discount(150,5)=142.5
        assert total == 142.5

    def test_total_invalid_coupon(self):
        self.cart.add_item("item", unit_price=100)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")
