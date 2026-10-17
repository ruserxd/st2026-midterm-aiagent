import pytest
import cart

# apply_discount tests
@pytest.mark.parametrize("price,percent,expected", [
    (200,15,170.00),
    (100,0,100.00),
    (50,100,0.00),
])
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price,percent", [
    (-10, 20),
    (100, -5),
    (100, 105),
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize("qty,expected", [
    (5,0),
    (10,5),
    (25,5),
    (50,10),
    (75,10),
    (100,15),
    (150,15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0,-5,3.7])
def test_bulk_discount_percent_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(int(qty))

# parse_coupon tests
@pytest.mark.parametrize("code,expected", [
    ("SAVE10",10),
    ("save20",20),
    (" SAVE30 ",30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["BAD10","SAVE0","SAVE51","SAVEXY","  "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal,member,expected", [
    (0,False,60),
    (500,True,30),
    (1000,False,0),
    (1500,True,0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1,-10.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart tests
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_add_and_items(self):
        self.c.add_item("apple", 1.0, 2)
        assert self.c.items() == {"apple":2}
        # add same item with same price increments quantity
        self.c.add_item("apple", 1.0, 3)
        assert self.c.items() == {"apple":5}
        # adding new item
        self.c.add_item("banana", 0.5, 4)
        assert self.c.items() == {"apple":5,"banana":4}

    def test_add_invalid(self):
        with pytest.raises(ValueError):
            self.c.add_item("orange", -1.0, 1)
        with pytest.raises(ValueError):
            self.c.add_item("orange", 1.0, 0)
        # different unit price for existing item
        self.c.add_item("pear", 2.0, 1)
        with pytest.raises(ValueError):
            self.c.add_item("pear", 3.0, 1)

    def test_remove(self):
        self.c.add_item("milk", 3.0, 5)
        self.c.remove_item("milk", 2)
        assert self.c.items() == {"milk":3}
        # remove remaining quantity
        self.c.remove_item("milk", 3)
        assert "milk" not in self.c.items()

    def test_remove_invalid(self):
        with pytest.raises(KeyError):
            self.c.remove_item("nonexistent",1)

    def test_subtotal(self):
        # quantities 5 -> no discount, 10->5%, 55->10%
        self.c.add_item("A", 10.0, 5)   # 50
        self.c.add_item("B", 20.0, 10)  # 200 * .95 =190
        self.c.add_item("C", 30.0, 55)  # 1650 * .90=1485
        assert self.c.subtotal() == round(50+190+1485,2)

    def test_total_no_coupon(self):
        self.c.add_item("A", 100.0, 1)
        amount = self.c.total(member=False, coupon=None)
        # subtotal=100, no coupon, shipping fee 60
        assert amount == round(100+60,2)

    def test_total_with_coupon_and_member(self):
        self.c.add_item("A", 200.0, 1)
        amt = self.c.total(member=True, coupon="SAVE20")
        # subtotal=200, coupon 20% =>160, shipping fee 30 (member)
        assert amt == round(160+30,2)

    def test_total_empty_cart(self):
        assert self.c.total() == 0.00
