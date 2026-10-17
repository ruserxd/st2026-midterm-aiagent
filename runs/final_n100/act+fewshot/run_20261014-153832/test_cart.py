import pytest
import cart

# ----- Helper data -----
@pytest.fixture
def simple_cart():
    c = cart.Cart()
    c.add_item("apple", 100, 5)   # 5 apples @100 each
    return c

# ---- apply_discount tests ----
@ pytest.mark.parametrize("price, percent, expected", [
    (200, 15, 170.0),
    (50, 0, 50.0),
    (50, 100, 0.0),
])
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@ pytest.mark.parametrize("price, percent", [(-10, 20), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---- bulk_discount_percent tests ----
@ pytest.mark.parametrize("quantity, expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@ pytest.mark.parametrize("quantity", [0, -5, 3.2])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---- parse_coupon tests ----
@pytest.mark.parametrize("code, percent", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, percent):
    assert cart.parse_coupon(code) == percent

@pytest.mark.parametrize("code", ["", "SAVEX", "SAVE0", "SAVE51", "ABC10", "123"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---- shipping_fee tests ----
@ pytest.mark.parametrize("subtotal, member, expected", [
    (500, False, 60),
    (500, True, 30),
    (1000, False, 0),
    (1200, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@ pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Cart tests ----
def test_cart_add_and_items(simple_cart):
    items = simple_cart.items()
    assert items["apple"] == 5

def test_cart_duplicate_add_increases_quantity():
    c=cart.Cart();c.add_item("banana",20,2);c.add_item("banana",20,3)
    assert c.items()["banana"]==5

@pytest.mark.parametrize("name, unit_price, quantity", [
    ("orange", -10, 1),
    ("orange", 10, 0),
    ("orange", 10, -3),
])
def test_cart_add_invalid(name, unit_price, quantity):
    c=cart.Cart()
    with pytest.raises(ValueError):
        c.add_item(name, unit_price, quantity)

@pytest.mark.parametrize("name, new_price", [
    ("apple", 120),
    ("pear", 10),
])
def test_cart_add_wrong_price_diff_name(name, new_price):
    c=cart.Cart();c.add_item("apple",100,1)
    if name=="apple":
        with pytest.raises(ValueError):
            c.add_item(name,new_price,1)
    else:
        # attempting to remove non-existing item should raise KeyError
        with pytest.raises(KeyError):
            c.remove_item(name,1)

def test_cart_remove_item(simple_cart):
    simple_cart.remove_item("apple",3)
    assert simple_cart.items()["apple"]==2

def test_cart_remove_more_than_exists(simple_cart):
    simple_cart.remove_item("apple",10)  # should remove fully
    assert "apple" not in simple_cart.items()

def test_cart_remove_nonexistent():
    c=cart.Cart();c.add_item("apple",100,1)
    with pytest.raises(KeyError):
        c.remove_item("banana",1)

def test_cart_subtotal_no_discount(simple_cart):
    # 5 apples @100 each = 500; no bulk discount (qty<10)
    assert simple_cart.subtotal()==500.0

def test_cart_subtotal_with_bulk():
    c=cart.Cart();c.add_item("apple",100,15)  # qty 15 =>5% off subtotal 1500
    assert c.subtotal()==1425.0

def test_cart_total_no_coupon_nonmember(simple_cart):
    # subtotal 500, no coupon, shipping 60 = total 560
    assert simple_cart.total(member=False,coupon=None)==560.0

def test_cart_total_with_coupon_and_member():
    c=cart.Cart();c.add_item("apple",100,10)  # qty 10 =>5% off subtotal 950
    coupon_percent = cart.parse_coupon("SAVE10")  # 10%
    # after coupon: 950 *0.9 = 855
    # shipping member half of 60 =30; total=885
    assert c.total(member=True,coupon="SAVE10")==885.0

def test_cart_total_empty_cart():
    c=cart.Cart()
    assert c.total()==0

def test_cart_total_invalid_coupon(simple_cart):
    with pytest.raises(ValueError):
        simple_cart.total(coupon="BADCODE")
