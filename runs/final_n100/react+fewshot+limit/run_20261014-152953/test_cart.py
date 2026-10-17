import pytest
import cart

# apply_discount
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
        (123.45, 20, round(123.45 * 0.8, 2)),
    ],
)
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 150])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# bulk_discount_percent
@pytest.mark.parametrize(
    "quantity,expected",
    [ (9,0), (10,5), (49,5), (50,10), (99,10), (100,15), (200,15) ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 2.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10",10),
        ("save20",20),
        (" SAVE30 ",30),
        ("sAvE5",5),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVExx", "SAVE0", "SAVE51", "XYZ10", "SAVE -10"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [ (500, False, 60), (500, True, 30), (1000, False, 0), (1500, True, 0) ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart class tests
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_add_and_items(self):
        self.c.add_item("apple", 2.0, 3)
        assert self.c.items() == {"apple":3}
        # adding same item increases quantity
        self.c.add_item("apple", 2.0, 2)
        assert self.c.items() == {"apple":5}
        # adding new item
        self.c.add_item("banana", 1.5)
        assert self.c.items() == {"apple":5, "banana":1}

    def test_add_invalid(self):
        with pytest.raises(ValueError):
            self.c.add_item("pear", -1.0, 2)
        with pytest.raises(ValueError):
            self.c.add_item("pear", 1.0, 0)
        with pytest.raises(ValueError):
            self.c.add_item("pear", 1.0, 2.5)

    def test_add_same_price_mismatch(self):
        self.c.add_item("orange", 3.0, 1)
        with pytest.raises(ValueError):
            self.c.add_item("orange", 3.5, 1)

    def test_remove_item(self):
        self.c.add_item("milk", 2.5, 4)
        self.c.remove_item("milk", 2)
        assert self.c.items() == {"milk":2}
        # remove remaining quantity
        self.c.remove_item("milk", 2)
        assert "milk" not in self.c.items()

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.c.remove_item("nonexistent", 1)

    def test_subtotal_and_bulk_discount(self):
        # item with bulk discount: quantity=10 => 5% off
        self.c.add_item("widget", 20.0, 10)  # base =200, discount 5%=10 ->190
        assert self.c.subtotal() == 190.0
        # add another without discount
        self.c.add_item("gadget", 15.0, 3)
        expected = round(190.0 + (15.0*3),2)  # no discount for gadget
        assert self.c.subtotal() == expected

    def test_total_without_coupon_and_member(self):
        self.c.add_item("item", 100.0, 1)
        # subtotal 100, shipping 60 -> total 160
        assert self.c.total(member=False) == 160.0

    def test_total_with_coupon_and_member(self):
        self.c.add_item("expensive", 200.0, 1)
        # subtotal 200, apply coupon SAVE10 => 180, shipping 60 -> total 240
        assert self.c.total(member=False, coupon="SAVE10") == 240.0
        # member gets half shipping: 30
        assert self.c.total(member=True, coupon="SAVE10") == 210.0

    def test_total_empty_cart(self):
        assert self.c.total() == 0.0
