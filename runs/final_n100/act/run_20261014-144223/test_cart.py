import pytest
import cart

# helper for floating comparison

def approx(a,b,eps=1e-9):
    return abs(a-b)<eps

# ---------- apply_discount ----------

@pytest.mark.parametrize("price,percent,result", [
    (200,15,170.0),
    (100,0,100.0),
    (50,100,0.0),
])
def test_apply_discount_success(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [
    (-1,10),
    (100,-5),
    (200,105),
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------

@pytest.mark.parametrize("qty,expected", [
    (9,0),
    (10,5),
    (49,5),
    (50,10),
    (99,10),
    (100,15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [-1,0,2.5, "a"])
def test_bulk_discount_errors(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- parse_coupon ----------

@pytest.mark.parametrize("code,result", [
    ("SAVE10",10),
    ("  save5 ",5),
    ("SaVe50",50),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", ["SAVEX", "SAVE0", "SAVE51", "123", "" ])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------

@pytest.mark.parametrize("subtotal,member,result", [
    (1000, False, 0),
    (999.99, False, 60),
    (999.99, True, 30),
])
def test_shipping_fee(subtotal, member, result):
    assert cart.shipping_fee(subtotal, member) == result

@pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class behaviour ----------

def test_cart_add_remove_and_totals():
    c = cart.Cart()
    assert list(c.items()) == []

    c.add_item('apple', 100, quantity=3)  # 300
    c.add_item('banana', 50)             # 50
    assert set(name for name,_ in c.items()) == {'apple','banana'}

    # subtotal
    assert c.subtotal() == 350

    # member total without coupon
    total = c.total(member=True)
    # no discount, shipping fee 30 => 380
    assert total == 350 + 30

    # add bulk quantity discount for banana (quantity=1 <10 ->0%)
    # add more bananas to reach 10
    c.add_item('banana', 50, quantity=9)  # +450
    assert c.subtotal() == 800
    assert cart.bulk_discount_percent(10) == 5

    total = c.total(member=False)
    # 5% discount on banana subtotal 500 => 475, apple 300 unchanged
    # subtotal after discounts: 775; shipping 60 -> 835
    assert approx(total, 835.0)

    # test coupon applies after bulk discount but before shipping
    c2 = cart.Cart()
    c2.add_item('item', 200, quantity=10)  # 2000
    # bulk discount 5% -> 1900
    total1 = c2.total(coupon='SAVE20')
    assert approx(total1, 1900 * 0.8)

    # shipping free for subtotal >=1000 before coupon? specification unclear; tests assume after discounts
    # here subtotal is 2000, so free regardless of coupon.
    c3 = cart.Cart()
    c3.add_item('expensive', 1200)
    assert c3.total() == 1200  # shipping fee 0

# Test that remove reduces quantity or deletes item

def test_cart_remove():
    c = cart.Cart()
    c.add_item('x', 10, quantity=5)
    c.remove_item('x')  # default qty=1
    assert next(q for _,q in c.items() if _=='x') == 4
    c.remove_item('x', quantity=4)
    assert list(c.items()) == []
