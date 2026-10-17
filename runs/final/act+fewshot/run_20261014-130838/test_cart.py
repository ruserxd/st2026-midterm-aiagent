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

# invalid price < 0
with pytest.raises(ValueError):
    cart.apply_discount(-5, 10)
# invalid percent out of bounds
for p in [-1, 101]:
    with pytest.raises(ValueError):
        cart.apply_discount(100, p)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize("quantity,percent", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(quantity, percent):
    assert cart.bulk_discount_percent(quantity) == percent
# invalid quantity
for q in [0, -5]:
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(q)

# ---------- parse_coupon ----------
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon(code, result):
    assert cart.parse_coupon(code) == result
# invalid formats
for bad in ["SAVExx", "SAVEBIG", "", "SAVE0", "SAVE51"]:
    with pytest.raises(ValueError):
        cart.parse_coupon(bad)

# ---------- shipping_fee ----------
@pytest.mark.parametrize("subtotal,member,fee", [
    (999, False, 60),
    (1000, False, 0),
    (1500, True, 0),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, fee):
    assert cart.shipping_fee(subtotal, member) == fee
# invalid subtotal
with pytest.raises(ValueError):
    cart.shipping_fee(-10)

# ---------- Cart operations and total calculations ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_total_zero(self):
        assert self.cart.total() == 0.0

    def test_add_and_items(self):
        self.cart.add_item("apple", 1.00, 3)
        self.cart.add_item("banana", 0.50, 2)
        items = self.cart.items()
        assert len(items) == 2
        assert any(it["name"] == "apple" and it["quantity"] == 3 for it in items)

    def test_remove_item_partial(self):
        self.cart.add_item("apple", 1.00, 5)
        self.cart.remove_item("apple", 2)
        assert next(it for it in self.cart.items() if it["name"] == "apple")['quantity'] == 3

    def test_remove_item_full(self):
        self.cart.add_item("pear", 0.80, 2)
        self.cart.remove_item("pear", 5)  # more than present
        assert all(it["name"] != "pear" for it in self.cart.items())

    def test_subtotal(self):
        self.cart.add_item("item", 10.0, 4)
        assert self.cart.subtotal() == 40.0

    def test_total_with_coupon_and_shipping(self):
        # add items totaling 200
        self.cart.add_item("product", 20.0, 10)  # bulk discount percent = 5 but not applied automatically
        # subtotal = 200
        # coupon SAVE10 gives 10% off: 180
        # shipping fee on 180 (non-member): 60 => total 240
        assert self.cart.total(coupon="SAVE10") == 240.0

    def test_total_member_no_shipping(self):
        self.cart.add_item("expensive", 500.0, 3)  # subtotal 1500
        assert self.cart.total(member=True) == 1500.0  # free shipping because >=1000

    def test_invalid_coupon_raises(self):
        self.cart.add_item("item", 10.0, 1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")
