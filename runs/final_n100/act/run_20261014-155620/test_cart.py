import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# --- apply_discount ---
@ pytest.mark.parametrize(
    "price,percent",[(200,15),(100,0),(100,100)],
)
def test_apply_discount_value(price, percent):
    result=apply_discount(price,percent)
    assert isinstance(result,float)

@pytest.mark.parametrize("price,percent",
    [(-10,5),(50,-1),(50,101)],
)
def test_apply_discount_error(price,percent):
    with pytest.raises(ValueError):
        apply_discount(price,percent)

# --- bulk_discount_percent ---
@ pytest.mark.parametrize("quantity,expected",[(0,None),(5,None)])
def test_bulk_discount_invalid(quantity,expected):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# --- parse_coupon ---
@pytest.mark.parametrize("code",["SAVE10","  save20 ","SaVe30"])
def test_parse_coupon_valid(code):
    result=parse_coupon(code)
    assert isinstance(result,int) and 1<=result<=50

@pytest.mark.parametrize("code",["SAV10","SAVE0","SAVE51","123"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# --- shipping_fee ---
@ pytest.mark.parametrize("subtotal,member,expected",
    [(1000,False,0),(1500,True,0),(999.99,False,60),(500,True,30)])
def test_shipping_fee(subtotal,member,expected):
    assert shipping_fee(subtotal,member)==expected

# --- Cart basic interface ---
def test_cart_structure():
    c=Cart()
    assert hasattr(c,"items") and callable(c.items)
    assert hasattr(c,"subtotal") and callable(c.subtotal)
    assert hasattr(c,"total") and callable(c.total)
