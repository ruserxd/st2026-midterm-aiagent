import pytest
import cart

# ---------- Utility ----------
@pytest.fixture
def new_cart():
    return cart.Cart()

# ---------- apply_discount ----------
@staticmethod
@pytest.mark.parametrize("price,percent,result",[
    (200,15,170.0),
    (100,0,100.0),
    (50,100,0.0)
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@staticmethod
@pytest.mark.parametrize("price,percent",[
    (-10,20),
    (100,-5),
    (100,105)
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------
@staticmethod
@pytest.mark.parametrize("qty,percent",[
    (9,0),
    (10,5),
    (49,5),
    (50,10),
    (99,10),
    (100,15)
])
def test_bulk_discount_percent(qty, percent):
    assert cart.bulk_discount_percent(qty) == percent

@staticmethod
@pytest.mark.parametrize("qty",[0,-1,2.5])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- parse_coupon ----------
@staticmethod
@pytest.mark.parametrize("code,result",[
    ("SAVE10",10),
    ("save5 ",5),
    ("  SAVE50",50),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

@staticmethod
@pytest.mark.parametrize("code",["SAVEX", "SAVE0", "SAVE51", "foo", "save-5"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@staticmethod
@pytest.mark.parametrize("subtotal,member,fee",[
    (1200,False,0),
    (1200,True,0),
    (999,False,60),
    (999,True,30),
])
def test_shipping_fee(subtotal, member, fee):
    assert cart.shipping_fee(subtotal, member) == fee

@staticmethod
@pytest.mark.parametrize("subtotal",[-10,-1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class behaviour ----------
@staticmethod
def test_cart_initial_empty(new_cart):
    assert new_cart.items() == {}
    assert new_cart.subtotal() == 0.0
    assert new_cart.total() == 0.0

@staticmethod
def test_add_item_and_subtotal(new_cart):
    new_cart.add_item("apple", 2, 3)      # 6 total, qty=3 -> no bulk
    new_cart.add_item("banana", 5, 10)   # 50 total, qty=10 -> 5% discount
    # subtotal: apple = 6.00, banana after 5% = 47.5
    assert new_cart.items() == {"apple":3,"banana":10}
    assert new_cart.subtotal() == round(6+47.5,2)

@staticmethod
def test_add_existing_item_increases_quantity(new_cart):
    new_cart.add_item("cherry", 1, 4)   # qty 4 -> no discount
    new_cart.add_item("cherry", 1, 7)   # total qty 11 -> 5% discount
    assert new_cart.items()["cherry"] == 11
    expected = round(1*11*(1-0.05),2)
    assert new_cart.subtotal() == expected

@staticmethod
def test_add_item_invalid_price_quantity(new_cart):
    with pytest.raises(ValueError):
        new_cart.add_item("invalid", -5, 1)
    with pytest.raises(ValueError):
        new_cart.add_item("invalid2", 5, 0)

@staticmethod
def test_remove_item(new_cart):
    new_cart.add_item("x", 3, 4)
    new_cart.remove_item("x", 2)   # qty left 2
    assert new_cart.items()["x"] == 2
    new_cart.remove_item("x", 2)   # should remove entirely
    assert "x" not in new_cart.items()

@staticmethod
def test_remove_nonexistent_raises(new_cart):
    with pytest.raises(KeyError):
        new_cart.remove_item("y",1)

@staticmethod
def test_total_with_coupon_and_member(new_cart):
    new_cart.add_item("item", 100, 10)   # qty 10 -> 5% bulk discount
    subtotal = 100*10*(1-0.05)          # 950
    total_no_coupon = round(subtotal + cart.shipping_fee(subtotal, member=True),2)
    # apply coupon 20%
    total_with_coupon = round((subtotal - subtotal*0.20)+cart.shipping_fee(subtotal- subtotal*0.20, member=True),2)
    assert new_cart.total(member=True, coupon="SAVE20") == total_with_coupon
    # no coupon
    assert new_cart.total(member=True) == total_no_coupon

@staticmethod
def test_total_invalid_coupon(new_cart):
    with pytest.raises(ValueError):
        new_cart.total(coupon="BADCODE")
