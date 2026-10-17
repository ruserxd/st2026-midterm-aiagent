import pytest
import cart

# apply_discount tests

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

def test_apply_discount_rounding():
    # 123 with 99% discount -> 1.17 after rounding to 2 decimals
    assert cart.apply_discount(123, 99) == 1.17

@pytest.mark.parametrize("price", [-10, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [101, -1, 200])
def test_apply_discount_percent_out_of_range(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# bulk_discount_percent tests

def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

@pytest.mark.parametrize("qty", [0, -1, 2.5])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# parse_coupon tests

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon(" save20 ") == 20
    assert cart.parse_coupon("SaVe5") == 5

@pytest.mark.parametrize("code", ["SAVEX", "save0", "save51", "invalid", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests

def test_shipping_fee():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(200, member=True) == 30
    assert cart.shipping_fee(800, member=False) == 60

@pytest.mark.parametrize("sub", [-1, -50])
def test_shipping_negative(sub):
    with pytest.raises(ValueError):
        cart.shipping_fee(sub)

# Cart class tests

def test_cart_add_and_subtotal():
    c = cart.Cart()
    c.add_item("apple", 2.5, quantity=3)
    c.add_item("banana", 1.0, quantity=5)
    assert c.subtotal() == pytest.approx(2.5*3 + 1.0*5)

@pytest.mark.parametrize("name,price,qty", [
     ("apple", 3.0, 2),
])
def test_cart_add_same_name_different_price(name, price, qty):
    c = cart.Cart()
    c.add_item(name, 1.0)
    with pytest.raises(ValueError):
        c.add_item(name, price, quantity=qty)

@pytest.mark.parametrize("name,qty", [(
     "apple", 2),
])
def test_cart_remove_items(name, qty):
    c = cart.Cart()
    c.add_item(name, 1.5, quantity=3)
    # before removal quantity is 3
    c.remove_item(name, quantity=qty)
    assert [item['quantity'] for item in c.items() if item['name']==name][0] == 3-qty

@pytest.mark.parametrize("name", ["pear"])
def test_cart_remove_nonexistent(name):
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item(name)

# Cart total tests including discounts and coupons

def test_cart_total_no_discounts():
    c = cart.Cart()
    c.add_item("item", 100, quantity=1)
    assert c.total() == 160.0  # subtotal 100 + shipping 60

def test_cart_total_bulk_discount_and_shipping_free():
    c = cart.Cart()
    c.add_item("i" , 10, quantity=200)  # <--- fix name
    # bulk discount 15% -> 1700, shipping free
    assert c.total() == pytest.approx(1700.
}
