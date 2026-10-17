import pytest
import cart

# ---------- apply_discount ----------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0

# boundary and rounding

def test_apply_discount_rounding():
    # 33.333... *2 -> 66.666..., round to 66.67
    assert cart.apply_discount(100, 33) == 66.7

@pytest.mark.parametrize("price,percent", [(-1, 10), (50,-5),(50,105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------

def test_bulk_discount_brackets():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@pytest.mark.parametrize("qty", [0,-1,3.5])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(int(qty))

# ---------- parse_coupon ----------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon(" save20 ") == 20
    assert cart.parse_coupon("SaVe50") == 50

@pytest.mark.parametrize("code", ["SAVE0","SAVE51","foo","SAVE-5"," SAVE " ,"SAVEB"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------

def test_shipping_fee():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(2000) == 0
    # member half
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(1200, member=True) == 0

@pytest.mark.parametrize("subtotal", [-1,-10.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ----------

def test_cart_add_and_items():
    c = cart.Cart()
    assert c.items() == {}
    c.add_item("apple", 0.5, quantity=3)
    assert c.items() == {"apple": 3}
    # adding same item increases qty
    c.add_item("apple", 0.5, quantity=2)
    assert c.items() == {"apple": 5}

    # price mismatch raises ValueError
    with pytest.raises(ValueError):
        c.add_item("apple", 0.6, quantity=1)

# remove tests

def test_cart_remove():
    c = cart.Cart()
    c.add_item("banana", 0.2, quantity=4)
    c.remove_item("banana", quantity=2)
    assert c.items() == {"banana": 2}
    # removing remaining qty removes item
    c.remove_item("banana", quantity=2)
    assert c.items() == {}
    # removing non-existent raises KeyError
    with pytest.raises(KeyError):
        c.remove_item("orange")

# subtotal calculation including bulk discount

def test_cart_subtotal():
    c = cart.Cart()
    # 10 apples at $1 each -> qty=10 gives 5% discount on $10 => $9.50
    c.add_item("apple", 1, quantity=10)
    assert c.subtotal() == 9.5
    # add 4 bananas $0.5 -> no bulk discount, $2
    c.add_item("banana", 0.5, quantity=4)
    assert c.subtotal() == 11.5  # 9.5 + 2 = 11.5

# total with coupon and shipping

def test_cart_total():
    c = cart.Cart()
    c.add_item("widget", 100, quantity=10)  # $1000 subtotal, bulk 5% -> $950
    assert c.subtotal() == 950.0
    # no coupon, non-member => shipping fee 60
    assert c.total(member=False) == 1010.0
    # member => shipping half 30
    assert c.total(member=True) == 980.0
    # apply coupon SAVE10 -> reduce 10%
    assert c.total(coupon="SAVE10") == 1045.0
    # coupon + member
    assert c.total(member=True, coupon="SAVE10") == 1015.0
    # empty cart total is 0
    e = cart.Cart()
    assert e.total() == 0

# invalid coupon on total raises ValueError

def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("item", 10)
    with pytest.raises(ValueError):
        c.total(coupon="BAD")
