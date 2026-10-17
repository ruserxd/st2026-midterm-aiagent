import pytest
import cart

# Helper to round floats consistently
def approx(value, rel=1e-9):
    return pytest.approx(value, rel=rel)

@pytest.mark.parametrize("price,percent,result", [
    (200.0, 15.0, 170.0),
    (50.0, 0.0, 50.0),
    (100.0, 100.0, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == approx(result)

@pytest.mark.parametrize("price,percent", [(-10.0, 20.0), (50.0, -5.0), (50.0, 120.0)])
def test_apply_discount_invalid_args(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

@pytest.mark.parametrize("quantity,expected", [
    (1, 0),
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

@pytest.mark.parametrize("quantity", [0, -5, 3.2, "10"])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    ("save25", 25),
    ("   SaVe5   ", 5),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", [
    "",
    "SAV10",
    "SAVE-1",
    "save51",
    "12345",
    "S A V E 10",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

@pytest.mark.parametrize("subtotal,member,expected", [
    (0.0, False, 60),
    (999.99, False, 60),
    (1000.0, False, 0),
    (2000.0, True, 30),
    (500.5, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

@pytest.mark.parametrize("subtotal", [-1.0, -100.0])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart class tests
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_items(self):
        self.cart.add_item("apple", 1.0, quantity=3)
        self.cart.add_item("banana", 2.5)
        items = self.cart.items()
        assert len(items) == 2
        names = {i["name"] for i in items}
        assert names == {"apple", "banana"}
        apple = next(i for i in items if i["name"] == "apple")
        banana = next(i for i in items if i["name"] == "banana")
        assert apple["quantity"] == 3
        assert apple["unit_price"] == 1.0
        assert banana["quantity"] == 1
        assert banana["unit_price"] == 2.5

    def test_remove_item(self):
        self.cart.add_item("apple", 1.0, quantity=3)
        self.cart.remove_item("apple", quantity=2)
        items = self.cart.items()
        apple = items[0]
        assert apple["quantity"] == 1
        with pytest.raises(ValueError):
            self.cart.remove_item("apple", quantity=5)
        with pytest.raises(KeyError):
            self.cart.remove_item("banana")

    def test_subtotal(self):
        self.cart.add_item("item1", 10.0, quantity=2)
        self.cart.add_item("item2", 5.0, quantity=3)
        assert self.cart.subtotal() == approx(35.0)

    def test_total_without_discounts(self):
        self.cart.add_item("item1", 10.0, quantity=2)
        total = self.cart.total()
        assert total == approx(80.0)

    def test_total_with_member(self):
        self.cart.add_item("item1", 200.0, quantity=5)
        total = self.cart.total(member=True)
        assert total == approx(1000.0)

    def test_total_with_coupon_and_bulk(self):
        self.cart.add_item("item1", 10.0, quantity=10)
        total = self.cart.total(coupon="SAVE10")
        assert total == approx(145.5)

    def test_total_with_bulk_only(self):
        self.cart.add_item("item1", 20.0, quantity=50)
        total = self.cart.total()
        assert total == approx(150.0)

    def test_total_with_invalid_coupon(self):
        self.cart.add_item("item1", 5.0, quantity=2)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")
