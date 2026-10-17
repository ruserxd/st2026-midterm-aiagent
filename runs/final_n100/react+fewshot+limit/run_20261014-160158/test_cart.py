import pytest
import cart

# Helper: compare floats with round as spec says.

def approx_equal(a,b,eps=0.01):
    return abs(a-b) < eps

# Tests for apply_discount
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0)
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [(-1, 10),(50,-5),(30,105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize("qty,expected", [
    (9,0),
    (10,5),
    (49,5),
    (50,10),
    (99,10),
    (100,15)
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0,-1,3.5,"a"])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# parse_coupon tests
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    (" save5 ", 5),
    ("SaVe50", 50),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["",
                                 "SAVEX", "SAVE0", "SAVE51",
                                 "10SAVE", "SAVER", "   "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (500, True, 30),
    (999.99, False, 60),
    (1000, False, 0),
    (1500, True, 0)
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1,-100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart tests
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_add_item_new(self):
        self.c.add_item("apple", 1.5, 2)
        assert self.c.items() == {"apple":2}

    def test_add_item_increase(self):
        self.c.add_item("banana", 0.5, 3)
        self.c.add_item("banana", 0.5, 2)
        assert self.c.items() == {"banana":5}

    def test_add_item_price_mismatch(self):
        self.c.add_item("pear", 1.0, 1)
        with pytest.raises(ValueError):
            self.c.add_item("pear", 1.2, 1)

    def test_add_invalid(self):
        with pytest.raises(ValueError):
            self.c.add_item("orange", -1, 1)
        with pytest.raises(ValueError):
            self.c.add_item("orange", 1, 0)

    def test_remove_item_partial(self):
        self.c.add_item("mango", 2.0, 5)
        self.c.remove_item("mango", 3)
        assert self.c.items() == {"mango":2}

    def test_remove_item_full(self):
        self.c.add_item("grape", 0.8, 4)
        self.c.remove_item("grape", 4)
        assert self.c.items() == {}

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.c.remove_item("non",1)

    def test_subtotal_simple(self):
        self.c.add_item("soda", 1.2, 3)   # qty<10 = no bulk discount
        assert self.c.subtotal() == round(1.2*3,2)

    def test_subtotal_bulk(self):
        self.c.add_item("chips", 1.0, 15)  # qty>=10 =5% discount
        expected = round(1.0*15*(1-0.05),2)
        assert self.c.subtotal() == expected

    def test_total_no_coupon(self):
        self.c.add_item("tea", 2.5, 4) # subtotal 10
        # no coupon, shipping fee 60 (subtotal<1000)
        total = round(10 + 60,2)
        assert self.c.total() == total

    def test_total_with_coupon_and_member(self):
        self.c.add_item("coffee", 5.0, 200) # qty>=100 =15% bulk discount
        sub = round(5*200*(1-0.15),2)
        coupon_percent = cart.parse_coupon("SAVE10")
        after_coupon = round(sub*(1-coupon_percent/100),2)
        shipping = cart.shipping_fee(after_coupon, member=True)
        total = round(after_coupon + shipping,2)
        assert self.c.total(member=True, coupon="SAVE10") == total

    def test_total_empty_cart(self):
        assert self.c.total() == 0.0
