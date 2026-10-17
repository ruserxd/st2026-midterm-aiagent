import pytest
import cart

# ---------- helper for expected values ----------

# apply_discount
@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# invalid price
@pytest.mark.parametrize("price,percent", [(-1, 10), (-5, 0)])
def test_apply_discount_invalid_price(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# invalid percent
@pytest.mark.parametrize("price,percent", [(100, -1), (50, 101)])
def test_apply_discount_invalid_percent(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent
@pytest.mark.parametrize("quantity,expected", [
    (5, 0),
    (10, 5),
    (50, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# invalid quantity
@pytest.mark.parametrize("quantity", [0, -3, 1.5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(int(quantity)) if isinstance(quantity, int) else cart.bulk_discount_percent(quantity)

# parse_coupon
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save5", 5),
    (" SAVE50 ", 50),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "NOTAVALID", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee
@pytest.mark.parametrize("subtotal,member,expected", [
    (500, False, 60),
    (500, True, 30),
    (1000, False, 0),
    (1200, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# invalid subtotal
@pytest.mark.parametrize("subtotal", [-1, -100.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart class tests

def test_cart_initial_empty():
    c = cart.Cart()
    assert c.items() == []
    assert c.subtotal() == 0.0
    # total should be zero, no shipping
    assert c.total() == 0.0


def test_add_and_remove_items():
    c = cart.Cart()
    c.add_item("apple", 1.00, quantity=3)
    c.add_item("banana", 0.50, quantity=2)
    # items list contains two entries
    assert len(c.items()) == 2
    # subtotal
    assert c.subtotal() == (3*1.00 + 2*0.50)  # 4.0
    # remove one apple
    c.remove_item("apple", quantity=1)
    assert any(i["name"]=="apple" and i["quantity"]==2 for i in c.items())
    # remove all bananas
    c.remove_item("banana")
    assert not any(i["name"]=="banana" for i in c.items())


def test_cart_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("widget", 200.0, quantity=5)  # subtotal 1000
    # subtotal >= 1000, shipping free even after coupon
    total_no_coupon = c.total()
    assert total_no_coupon == 1000.0
    # with a valid coupon of 10%
    total_with_coupon = c.total(coupon="SAVE10")
    expected_after_discount = cart.apply_discount(1000, 10)  # 900.0
    # shipping should be free because subtotal after discount still >= 1000? 900 < 1000 so fee 60
    # but spec says shipping on amount from step 2, so 60 added
    assert total_with_coupon == round(expected_after_discount + cart.shipping_fee(expected_after_discount), 2)


def test_cart_total_member_shipping():
    c = cart.Cart()
    c.add_item("book", 120.0, quantity=1)  # subtotal 120
    # member should get half shipping
    assert c.total(member=True) == round(120 + cart.shipping_fee(120, True), 2)

# Test that empty cart returns zero without shipping

def test_empty_cart_total():
    c = cart.Cart()
    assert c.total() == 0.0
