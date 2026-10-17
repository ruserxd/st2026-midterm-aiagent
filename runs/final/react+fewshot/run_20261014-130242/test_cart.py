import pytest
import cart

# ---------- apply_discount ---------------------------------

def test_apply_discount_valid():
    assert cart.apply_discount(200, 15) == 170.0
    # round to two decimals
    assert cart.apply_discount(123.456, 10) == round(123.456 * 0.90, 2)

@ pytest.mark.parametrize("price, percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent -----------------------------

def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

@ pytest.mark.parametrize("qty", [0, -1, 3.5])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- parse_coupon -------------------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20 ") == 20
    assert cart.parse_coupon(" SAVE5") == 5

@ pytest.mark.parametrize("code", ["", "SAVEX", "SAVE0", "SAVE51", "ABC10"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee -------------------------------------

def test_shipping_fee():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(200, member=True) == 30

@ pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ---------------------------------------

def test_cart_initially_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

# adding items

def test_add_item_new_and_existing():
    c = cart.Cart()
    c.add_item("apple", 1.00, 2)
    assert c.items() == {"apple": 2}
    # add same item with same price increases quantity
    c.add_item("apple", 1.00, 3)
    assert c.items()["apple"] == 5

@ pytest.mark.parametrize("name, unit_price, qty", [
    ("banana", -0.5, 1),
    ("orange", 1.0, 0),
])
def test_add_item_invalid(name, unit_price, qty):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item(name, unit_price, qty)

@ pytest.mark.parametrize("name", ["pear"])
def test_add_item_price_mismatch(name):
    c = cart.Cart()
    c.add_item(name, 2.0, 1)
    with pytest.raises(ValueError):
        c.add_item(name, 3.0, 1)

# removing items

def test_remove_item():
    c = cart.Cart()
    c.add_item("tshirt", 20.0, 5)
    # remove some
    c.remove_item("tshirt", 2)
    assert c.items()["tshirt"] == 3
    # remove rest
    c.remove_item("tshirt", 3)
    assert "tshirt" not in c.items()

@ pytest.mark.parametrize("name, qty", [
    ("hat", 1),  # not present
])
def test_remove_nonexistent(name, qty):
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item(name, qty)

# subtotal calculation with bulk discount

def test_subtotal_with_bulk_discount():
    c = cart.Cart()
    # 9 items -> no bulk discount
    c.add_item("pen", 2.0, 9)
    assert c.subtotal() == 18.00
    # 10 items -> 5% discount on these 10 pens
    c.add_item("pencil", 1.0, 10)
    # pen subtotal stays same
    # pencil subtotal before discount: 10*1=10, after 5% =9
    assert c.subtotal() == round(18.00 + 9.00, 2)

# total with coupon and shipping

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("book", 30.0, 1)
    # subtotal 30
    total_no_coupons = c.total()  # no member, no coupon
    assert total_no_coupons == round(30 + cart.shipping_fee(30), 2)  # shipping 60
    # with valid coupon 10%
    total_with_coupon = c.total(coupon="SAVE10")
    discounted_amount = 30 * 0.90
    expected = round(discounted_amount + cart.shipping_fee(discounted_amount), 2)
    assert total_with_coupon == expected
    # member discount halves shipping
    total_member = c.total(member=True)
    expected_member = round(30 + cart.shipping_fee(30, member=True), 2)
    assert total_member == expected_member

# empty cart total should be zero no shipping

def test_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0

# coupon validation in total

def test_total_invalid_coupon():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
