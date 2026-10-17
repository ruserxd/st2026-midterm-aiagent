import pytest
import cart

# ---- apply_discount ----
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# boundaries for invalid inputs
@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---- bulk_discount_percent ----
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---- parse_coupon ----
valid_cases = {
    "SAVE10": 10,
    "save50": 50,
    " SAVE25 ": 25,
}
for code, expected in valid_cases.items():
    assert cart.parse_coupon(code) == expected

invalid_codes = ["SAV10", "SAVE0", "SAVE51", "", "  ", "abc", None]
for code in invalid_codes:
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---- shipping_fee ----
@pytest.mark.parametrize("subtotal,member,expected", [
    (1000, False, 0),
    (999.99, False, 60),
    (200, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

with pytest.raises(ValueError):
    cart.shipping_fee(-10)

# ---- Cart class ----
def test_cart_add_and_subtotal():
    c = cart.Cart()
    c.add_item("apple", 1.0, 5)   # bulk discount for 5 -> 0%
    assert c.items() == {"apple": 5}
    # add same item with same price
    c.add_item("apple", 1.0, 10)
    assert c.items() == {"apple": 15}
    # subtotal: 1*15 = 15; bulk discount for 15 -> 5% => 14.25
    assert c.subtotal() == pytest.approx(14.25, rel=1e-9)

    with pytest.raises(ValueError):
        c.add_item("apple", 2.0, 1)   # different price

    with pytest.raises(ValueError):
        c.add_item("banana", -1.0, 1)

    with pytest.raises(ValueError):
        c.add_item("banana", 1.0, 0)

# ---- Cart remove and total ----
def test_cart_remove_and_total():
    c = cart.Cart()
    c.add_item("item", 100, 5)   # subtotal 500
    # remove some
    c.remove_item("item", 2)
    assert c.items() == {"item": 3}
    # removing more than exists removes the item entirely
    c.remove_item("item", 5)
    assert c.items() == {}

    with pytest.raises(KeyError):
        c.remove_item("missing", 1)

    # test total with coupon and shipping
    c.add_item("prod", 200, 60)   # subtotal: 200*60=12000; bulk 15% -> 10200
    # after coupon SAVE10 -> 9180
    tot = c.total(member=False, coupon="SAVE10")
    assert tot == pytest.approx(9180 + cart.shipping_fee(9180), rel=1e-9)

    # member shipping free for high subtotal
    c.add_item("extra", 800, 1)   # new item increases subtotal beyond 1000? compute
    # compute expected
    sub = c.subtotal()
    assert c.total(member=True) == pytest.approx(sub + cart.shipping_fee(sub, member=True), rel=1e-9)

# ---- Edge cases: empty cart total -----
def test_empty_cart_total():
    c = cart.Cart()
    assert c.total() == 0.0
