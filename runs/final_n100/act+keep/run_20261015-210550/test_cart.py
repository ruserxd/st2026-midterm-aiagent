import pytest
from cart import apply_discount,bulk_discount_percent,parse_coupon,shipping_fee,Cart

# Helper functions not needed.

def test_apply_discount_valid():
    assert apply_discount(200,15) == 170.0
    assert apply_discount(100,0) == 100.0
    assert apply_discount(100,100) == 0.0
    # rounding check
    assert apply_discount(333.33, 10) == round(333.33*0.9,2)

@ pytest.mark.parametrize("price",[-1, -0.01])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        apply_discount(price,10)

@ pytest.mark.parametrize("percent",[-5, 150])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# bulk_discount_percent

def test_bulk_discount_percent():
    # quantity <10 -> 0% discount
    assert bulk_discount_percent(1) == 0.0
    # 10-20 ->5%
    assert bulk_discount_percent(15) == 5.0
    # 21-50 ->10%
    assert bulk_discount_percent(30) == 10.0
    # >50 ->20%
    assert bulk_discount_percent(60) == 20.0

# parse_coupon

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == {"type":"percentage","value":10}
    assert parse_coupon("FREESHIP") == {"type":"free_shipping","value":None}
    # coupon not found -> None
    assert parse_coupon("UNKNOWN") is None

# shipping_fee

def test_shipping_fee_non_member():
    # subtotal below 50 -> $5.99, but rounded to 2 decimals
    assert shipping_fee(30) == 5.99
    # subtotal above 50 -> free
    assert shipping_fee(100) == 0.0

@ pytest.mark.parametrize("member",[True])
def test_shipping_fee_member(member):
    assert shipping_fee(10, member=member) == 0.0

# Cart tests

def test_cart_basic_operations():
    c = Cart()
    c.add_item('apple',1.00,3)
    c.add_item('banana',0.5,2)
    assert len(c.items())==2
    # subtotal
    expected_subtotal= 3*1.00+2*0.5
    assert c.subtotal() == expected_subtotal
    # total without member/coupon
    assert c.total()==expected_subtotal+shipping_fee(expected_subtotal)


def test_cart_remove_item():
    c = Cart()
    c.add_item('apple',1.00,3)
    c.remove_item('apple',2)
    assert c.items()[0]['quantity']==1
    # removing more than present -> raise ValueError
    with pytest.raises(ValueError):
        c.remove_item('apple',5)


def test_cart_total_with_coupon_and_member():
    c=Cart()
    c.add_item('item',20,2)  # subtotal 40
    total = c.total(member=True,coupon='SAVE10')
    # apply coupon: 10% off => 36.0, then member free shipping
    assert total==36.0
