import pytest
import cart

# ---------- apply_discount ----------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price,percent", [(-1,10), (100,-5), (100,105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------

def test_bulk_discount_percent_values():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(100) == 15

@pytest.mark.parametrize("quantity", [0,-3,1.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(int(quantity)) if isinstance(quantity,int) else cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon(" save20 ") == 20
    assert cart.parse_coupon("SaVe1") == 1

@pytest.mark.parametrize("code", ["SAVe0","SAVE51","ABCD","", "12345"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------

def test_shipping_fee():
    assert cart.shipping_fee(1001) == 0
    assert cart.shipping_fee(999) == 60
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(200, member=False) == 60

@pytest.mark.parametrize("subtotal", [-10,-1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart.total logic ----------

def test_cart_total_no_items():
    c = cart.Cart()
    assert c.total() == 0.0

@pytest.mark.parametrize("items,coupon,member", [
    ([("item1",100,2)], None, False),   # subtotal 200 -> +60 shipping =260
    ([("item2",150,5)], "SAVE10", False), # subtotal 750 -> coupon 10% =>675 +60=735
    ([("item3",500,3)], None, True),    # subtotal 1500 free shipping
])
def test_cart_total_various(items,coupon,member):
    c = cart.Cart()
    for name, price, qty in items:
        c.add_item(name, price, qty)
    expected_subtotal = sum(p*q for _,p,q in items)
    after_coupon = expected_subtotal
    if coupon is not None:
        percent = cart.parse_coupon(coupon)
        after_coupon = round(after_coupon * (1 - percent/100), 2)
    shipping = 0 if expected_subtotal==0 else cart.shipping_fee(expected_subtotal, member=member)
    expected_total = round(after_coupon + shipping, 2)
    assert c.total(member=member, coupon=coupon) == expected_total

def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("item",50,1)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
