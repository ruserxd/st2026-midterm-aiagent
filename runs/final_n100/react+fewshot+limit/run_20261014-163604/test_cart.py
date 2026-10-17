import pytest
import cart

# ---- apply_discount ----
@pytest.mark.parametrize("price,percent,result",[
    (200,15,170.0),
    (100,0,100.0),
    (50,100,0.0),
])
def test_apply_discount(price,percent,result):
    assert cart.apply_discount(price, percent) == result

# invalid price <0
@pytest.mark.parametrize("price",[-1, -5.5])
def test_apply_discount_invalid_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

# invalid percent >100 or negative
@pytest.mark.parametrize("percent",[-10,101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(50, percent)

# ---- bulk_discount_percent ----
@pytest.mark.parametrize("quantity,expected",[
    (5,0),
    (10,5),
    (49,5),
    (50,10),
    (99,10),
    (100,15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# invalid quantity non-positive or not int
@pytest.mark.parametrize("quantity",[0,-1,2.5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---- parse_coupon ----
@pytest.mark.parametrize("code,result",[
    ("SAVE10",10),
    ("save20",20),
    (" SAVE30 ",30),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code",["SA VE10","SAVE0","SAVEX","save51",""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---- shipping_fee ----
@pytest.mark.parametrize("subtotal,member,result",[
    (1001,False,0),
    (1000,True,0),
    (999.99,False,60),
    (500,True,30),
])
def test_shipping_fee(subtotal, member, result):
    assert cart.shipping_fee(subtotal, member) == result

# invalid subtotal negative
@pytest.mark.parametrize("subtotal",[-1,-0.01])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Cart class ----
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_initially_empty(self):
        assert self.c.items() == {}
        assert self.c.subtotal() == 0
        assert self.c.total() == 0

    def test_add_and_items(self):
        self.c.add_item("apple",1.00,2)
        self.c.add_item("banana",0.50)
        assert self.c.items() == {"apple":2,"banana":1}

    def test_add_existing_increases_quantity_same_price(self):
        self.c.add_item("pear",3.00,1)
        self.c.add_item("pear",3.00,4)
        assert self.c.items()["pear"] == 5

    def test_add_existing_different_price_error(self):
        self.c.add_item("orange",2.00)
        with pytest.raises(ValueError):
            self.c.add_item("orange",3.00)

    def test_remove_decrease_and_remove_when_zero(self):
        self.c.add_item("mango",1.50,5)
        self.c.remove_item("mango",2)
        assert self.c.items()["mango"] == 3
        self.c.remove_item("mango",3)
        assert "mango" not in self.c.items()

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.c.remove_item("grape")

    def test_subtotal_with_bulk_discount(self):
        # 10 apples at $1 each -> bulk discount 5%
        self.c.add_item("apple",1.00,10)
        # subtotal before discount: 10*1=10
        # discount 5% => 0.50
        assert self.c.subtotal() == 9.5

    def test_total_with_coupon_and_shipping(self):
        self.c.add_item("widget",100.00,2)  # no bulk discount
        subtotal = 200
        coupon_percent = cart.parse_coupon("SAVE10")  # 10%
        after_coupon = subtotal * (1-0.10)
        shipping = cart.shipping_fee(after_coupon, member=False)
        total_expected = round(after_coupon + shipping,2)
        assert self.c.total(coupon="SAVE10") == total_expected
