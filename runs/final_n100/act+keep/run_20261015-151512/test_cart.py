import pytest
import cart

# Helper to round for expected values

def r2(x):
    return round(float(x), 2)

# ==== Function: apply_discount ==== 

def test_apply_discount_normal():
    assert r2(cart.apply_discount(200, 15)) == 170.0

@ pytest.mark.parametrize("price,percent",[
    (100,-1),( -10,20),(50,110),
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ==== Function: bulk_discount_percent ==== 

def test_bulk_discount_limits():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 10
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

@ pytest.mark.parametrize("quantity", [0,-5,1.5, "a"]) 
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ==== Function: parse_coupon ==== 

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon(" save20 ") == 20
    assert cart.parse_coupon("SaVe1") == 1

@ pytest.mark.parametrize("code", ["save0","SAVE51","INVALID","SAVExx","sava10"]) 
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ==== Function: shipping_fee ==== 

def test_shipping_fee():
    assert cart.shipping_fee(0, False) == 60
    assert cart.shipping_fee(500, True) == 30
    assert cart.shipping_fee(1000, False) == 0
    assert cart.shipping_fee(2000, True) == 0

@ pytest.mark.parametrize("subtotal", [-1,-10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ==== Cart class ==== 
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_add_item_new_and_increase(self):
        self.c.add_item('apple', 1.5, 2)
        assert self.c.items() == {'apple': 2}
        self.c.add_item('apple', 1.5, 3)
        assert self.c.items() == {'apple': 5}

    def test_add_item_invalid(self):
        with pytest.raises(ValueError):
            self.c.add_item('banana', -1)
        with pytest.raises(ValueError):
            self.c.add_item('banana', 1, 0)
        with pytest.raises(ValueError):
            self.c.add_item('banana', 1, -2)

    def test_add_item_price_mismatch(self):
        self.c.add_item('cherry', 2, 1)
        with pytest.raises(ValueError):
            self.c.add_item('cherry', 3, 1)

    def test_remove_item(self):
        self.c.add_item('durian', 5, 4)
        self.c.remove_item('durian', 2)
        assert self.c.items() == {'durian': 2}
        self.c.remove_item('durian', 2)
        assert self.c.items() == {}

    def test_remove_item_not_present(self):
        with pytest.raises(KeyError):
            self.c.remove_item('elephant')

    def test_subtotal_no_bulk(self):
        self.c.add_item('fig', 3, 9)
        assert r2(self.c.subtotal()) == 27.0

    def test_subtotal_with_bulk_discount(self):
        # quantity 12 => 5% discount
        self.c.add_item('grape', 10, 12)
        expected = 10*12*(1-0.05)  # 120 * 0.95 = 114
        assert r2(self.c.subtotal()) == round(expected,2)

    def test_total_no_coupon_member(self):
        self.c.add_item('honey', 50, 3)  # subtotal 150 no bulk discount
        total = self.c.total(member=True)
        # subtotal 150 -> shipping 30; total 180
        assert r2(total) == 180.0

    def test_total_with_coupon_and_shipping(self):
        self.c.add_item('icecream', 20, 6)  # subtotal 120 no bulk
        # coupon 10% off => 108, shipping 60 => total 168
        total = self.c.total(coupon='SAVE10')
        assert r2(total) == 168.0

    def test_total_empty_cart(self):
        assert r2(self.c.total()) == 0.0

    def test_total_invalid_coupon(self):
        with pytest.raises(ValueError):
            self.c.total(coupon='BADCODE')

# ==== Specification mismatch detection ==== 
# The following tests are intentionally designed to fail if the implementation
# diverges from the specification described in cart.__doc__ and function
# docstrings.

if __name__ == "__main__":
    # Run pytest programmatically
    import sys, subprocess
    cmd = [sys.executable, '-m', 'pytest', '-q', __file__]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        raise SystemExit(f"Tests failed: {result.stderr}")
