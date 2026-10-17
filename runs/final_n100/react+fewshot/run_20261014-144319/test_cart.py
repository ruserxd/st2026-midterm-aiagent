import pytest
import cart

# ---- apply_discount ---------------------------------------------------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),            # example from spec
    (100, 0, 100.00),           # no discount
    (50, 100, 0.0),             # full free
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# boundary checks for ValueError
@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_price_negative(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_percent_out_of_range(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---- bulk_discount_percent -------------------------------------------
@pytest.mark.parametrize("qty,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -5, 3.5, "10"])
def test_bulk_discount_invalid_quantity(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---- parse_coupon -----------------------------------------------------
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE5 ", 5),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", ["", "abc", "SAVE0", "SAVE51", "SAVEX"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---- shipping_fee -----------------------------------------------------
@pytest.mark.parametrize("subtotal,member,expected", [
    (999.99, False, 60),   # under threshold
    (1000, False, 0),      # at threshold
    (1500, True, 30),      # member gets half
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Cart class -------------------------------------------------------
def test_cart_initially_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

# adding items, including bulk discounts and price mismatch error
c = cart.Cart()
c.add_item("widget", 20.0, quantity=5)   # no bulk discount yet
assert c.items() == {"widget": 5}
assert c.subtotal() == 100.0  # 20*5
# add more to trigger 5% bulk discount for that item (quantity now 15)
c.add_item("widget", 20.0, quantity=10)
# unit price same -> allowed; new total: 20*(15)=300 with 5% off => 285
assert c.subtotal() == 285.0

# try adding item with different unit_price should raise ValueError
with pytest.raises(ValueError):
    c.add_item("widget", 25.0)

# remove items
c.remove_item("widget", quantity=5)  # remaining 10 units, still discounted 5%
c.assert_subtotal = c.subtotal()  # capture
assert c.items()["widget"] == 10
expected_after_remove = round(20*10*(1-0.05),2)
assert c.subtotal() == expected_after_remove

# removing more than present should delete the item completely
c.remove_item("widget", quantity=10)  # now zero -> removed
assert "widget" not in c.items()

# coupon and shipping integration
cart_with_coupon = cart.Cart()
cart_with_coupon.add_item("gadget", 100.0, quantity=2)  # subtotal 200 (no bulk)
# apply 20% coupon
amount_after_coupon = cart_with_coupon.total(coupon="SAVE20")
# amount should be 200 - 40 = 160 plus shipping 60 => 220 rounded
assert amount_after_coupon == round(160 + 60, 2)

# member discount on shipping
cart_member = cart.Cart()
cart_member.add_item("gizmo", 600.0)
# subtotal 600 < 1000 so shipping 60; member pays 30
assert cart_member.total(member=True) == round(600 + 30, 2)

# empty cart total should be 0 (no shipping)
c_empty = cart.Cart()
assert c_empty.total() == 0
