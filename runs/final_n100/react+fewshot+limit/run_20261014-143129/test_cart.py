import pytest
import cart

# apply_discount
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (100, 100, 0.0),
])
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [
    (-1, 10),
    (100, -5),
    (100, 105),
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent
@pytest.mark.parametrize("quantity,percent", [
    (1,0),(9,0),(10,5),(49,5),(50,10),(99,10),(100,15),(150,15),
])
def test_bulk_discount_percent(quantity, percent):
    assert cart.bulk_discount_percent(quantity) == percent

@pytest.mark.parametrize("quantity", [0,-1,1.5,"a"])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon
valid = {
    "SAVE10":10,
    "save20 ":20,
    "  SaVe1  ":1,
}
for code,exp in valid.items():
    def _test(code=code, exp=exp):
        assert cart.parse_coupon(code) == exp
    globals()[f"test_parse_{code.strip().replace(' ', '_')}"] = _test

@pytest.mark.parametrize("code", ["", "SAVEX", "SAVE0", "SAVE51", "NOTVALID", 123])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee
@pytest.mark.parametrize("subtotal,member,fee", [
    (1000, False, 0),
    (999.99, False, 60),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, fee):
    assert cart.shipping_fee(subtotal, member) == fee

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart tests
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0
        assert self.cart.total() == 0

    def test_add_item(self):
        self.cart.add_item("apple", 1.00, 3)
        assert self.cart.items() == {"apple":3}
        # adding same item increases quantity
        self.cart.add_item("apple", 1.00, 2)
        assert self.cart.items() == {"apple":5}
        # unit price mismatch raises
        with pytest.raises(ValueError):
            self.cart.add_item("apple", 1.10, 1)

    def test_remove_item(self):
        self.cart.add_item("banana", 0.50, 4)
        self.cart.remove_item("banana", 2)
        assert self.cart.items() == {"banana":2}
        # removing more than present removes item
        self.cart.remove_item("banana", 5)
        assert "banana" not in self.cart.items()
        with pytest.raises(KeyError):
            self.cart.remove_item("orange",1)

    def test_subtotal_with_discounts(self):
        # bulk discount for 10 units gives 5%
        self.cart.add_item("widget", 20.0, 10)
        # 20*10=200 minus 5% =190
        assert self.cart.subtotal() == 190.00
        # bulk discount for 55 units gives 10%
        self.cart.add_item("gadget", 5.0, 55)
        # gadget subtotal:5*55=275-10%=247.5
        assert self.cart.subtotal() == round(190+247.5,2)

    def test_total_with_coupon_and_shipping(self):
        self.cart.add_item("item", 200.0, 1)  # no bulk discount
        # subtotal 200
        total = self.cart.total(coupon="SAVE10")
        # after coupon:200-20=180, shipping 60 ->240
        assert total == 240.00
        # member reduces shipping to 30
        assert self.cart.total(member=True) == 260.0
        # free shipping on high subtotal
        self.cart = cart.Cart()
        self.cart.add_item("expensive", 1200,1)
        assert self.cart.total() == 1200.0
