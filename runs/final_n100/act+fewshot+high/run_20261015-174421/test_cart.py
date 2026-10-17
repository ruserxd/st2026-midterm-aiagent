import pytest
import cart

def test_apply_discount_basic():
    assert cart.apply_discount(200,15) == 170.0

def test_apply_discount_rounding():
    assert cart.apply_discount(100,33) == 67.0

@pytest.mark.parametrize("price,percent", [
    (-10,5),
    (10,-1),
    (10,101)
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

@pytest.mark.parametrize("qty,expected", [
    (5,0),
    (10,5),
    (50,10),  # spec expects 10
    (51,10),
    (100,15)
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0,-1,"10",2.5])
def test_bulk_discount_percent_errors(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

def test_parse_coupon_basic():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon(" SAVE30 ") == 30

def test_parse_coupon_case_insensitive():
    # spec: case‑insensitive
    assert cart.parse_coupon("save20") == 20

@pytest.mark.parametrize("code", ["DISCOUNT5","SAVE0","SAVE51","SAVE-5"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

def test_shipping_fee():
    # Assuming thresholds as per spec
    assert cart.shipping_fee(500) == 60
    assert cart.shipping_fee(1500) == 0
    assert cart.shipping_fee(200, member=True) == 30

def test_shipping_fee_negative():
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

def test_cart_initial_empty():
    c = cart.Cart()
    assert c.items() == {}

def test_add_and_subtotal():
    c = cart.Cart()
    c.add_item("apple",2,5)
    assert c.items() == {"apple":5}
    assert c.subtotal() == 10.0
    c.add_item("banana",1,12)
    assert c.items() == {"apple":5,"banana":12}
    # banana gets 5% discount: line total 11.4
    assert c.subtotal() == 21.4

def test_add_item_errors():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("bad", -1, 5)
    with pytest.raises(ValueError):
        c.add_item("bad2", 10, 0)
    with pytest.raises(ValueError):
        c.add_item("bad3", 10, "3")
    # Same name different price
    c.add_item("apple",2,5)
    with pytest.raises(ValueError):
        c.add_item("apple",3,1)

def test_remove_and_subtotal():
    c = cart.Cart()
    c.add_item("apple",2,5)
    c.add_item("banana",1,12)
    c.remove_item("apple",3)
    assert c.items() == {"apple":2,"banana":12}
    assert c.subtotal() == 15.4
    # Remove remaining quantity of apple; spec expects removal
    c.remove_item("apple",2)
    assert "apple" not in c.items()
    with pytest.raises(KeyError):
        c.remove_item("orange",1)

def test_total_basic():
    c = cart.Cart()
    c.add_item("apple",2,5)
    c.add_item("banana",1,12)
    assert c.total() == pytest.approx(81.4)
    assert c.total(member=True) == pytest.approx(51.4)

def test_total_coupon():
    c = cart.Cart()
    c.add_item("apple",2,5)
    c.add_item("banana",1,12)
    assert c.total(coupon="SAVE10") == pytest.approx(79.26)
    assert c.total(member=True,coupon="SAVE10") == pytest.approx(49.26)

def test_total_shipping_fee_after_coupon():
    c = cart.Cart()
    # subtotal 1200
    c.add_item("expensive",200,6)  # 6*200=1200
    expected_amount = cart.apply_discount(1200,50)  # 600
    expected_fee = cart.shipping_fee(expected_amount)
    expected_total = round(expected_amount + expected_fee,2)
    assert c.total(coupon="SAVE50") == pytest.approx(expected_total)

def test_total_empty():
    c = cart.Cart()
    assert c.total() == 0

def test_total_invalid_coupon():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
