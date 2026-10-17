import pytest
import cart

# ---------- Utility helpers for expected calculations ----------

def expected_bulk_discount(quantity):
    if quantity >= 100:
        return 15
    if quantity >= 50:
        return 10
    if quantity >= 10:
        return 5
    return 0

# ---------- Tests for standalone functions ----------

def test_apply_discount_valid():
    assert cart.apply_discount(200, 15) == 170.00
    assert cart.apply_discount(100, 0) == 100.00
    assert cart.apply_discount(50, 100) == 0.00

@pytest.mark.parametrize("price,percent", [(-1,10), (10,-5), (10,110)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)


def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

@pytest.mark.parametrize("qty", [0, -3])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)


def test_parse_coupon_valid():
    assert cart.parse_coupon('SAVE10') == 10
    assert cart.parse_coupon('  save5 ') == 5
    assert cart.parse_coupon('sAvE50') == 50

@pytest.mark.parametrize("code", ["", "SAVExx", "SAVEX51", "123", "NOPE10"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)


def test_shipping_fee():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(2000) == 0

@pytest.mark.parametrize("sub", [-10])
def test_shipping_fee_invalid(sub):
    with pytest.raises(ValueError):
        cart.shipping_fee(sub)

# ---------- Tests for Cart class ----------

@staticmethod
class DummyCart:
    pass


def test_cart_initially_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.00
    assert c.total() == 0.00


def test_add_item_and_subtotal():
    c = cart.Cart()
    c.add_item('apple', 1.20, quantity=5)
    # bulk discount: 5 items -> 0%
    expected = round(1.20*5*(1-0/100),2)
    assert c.subtotal() == expected
    assert c.items() == {'apple':5}

    c.add_item('apple', 1.20, quantity=7)  # total 12 -> bulk discount 5%
    exp = round(1.20*12*(1-5/100),2)
    assert c.subtotal() == exp
    assert c.items()['apple'] == 12


def test_add_item_different_price_error():
    c=cart.Cart()
    c.add_item('banana',0.50)
    with pytest.raises(ValueError):
        c.add_item('banana',0.60)


def test_remove_item_and_automatic_removal():
    c = cart.Cart()
    c.add_item('carrot', 2.00, quantity=3)
    c.remove_item('carrot')  # remove 1 -> 2 left
    assert c.items()['carrot'] == 2
    c.remove_item('carrot', quantity=2)  # zero left, should be removed
    assert 'carrot' not in c.items()

    with pytest.raises(KeyError):
        c.remove_item('dragonfruit')


def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item('widget', 100.00, quantity=5)   # subtotal 500, no bulk discount
    total_before_coupon = round(500 + 60,2)      # shipping fee 60
    assert c.total() == total_before_coupon

    coupon_total = cart.Cart()
    coupon_total.add_item('widget',100.00,quantity=5)
    subtotal = 500
    discounted = round(subtotal*0.90,2)   # SAVE10 -> 10%
    shipping = 60
    assert coupon_total.total(coupon='SAVE10') == round(discounted+shipping,2)


def test_empty_cart_no_shipping():
    c=cart.Cart()
    assert c.total() == 0.00


def test_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item('item',10)
    with pytest.raises(ValueError):
        c.total(coupon='BADCODE')
