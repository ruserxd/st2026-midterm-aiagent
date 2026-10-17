import pytest
import cart

# Helper for floating comparison
EPS = 1e-6

def assert_close(a, b):
    assert abs(a - b) < EPS

# ----- apply_discount -----
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [
    (-10, 20),
    (100, -5),
    (100, 105),
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ----- bulk_discount_percent -----
@pytest.mark.parametrize("quantity,percent", [
    (5, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, percent):
    assert cart.bulk_discount_percent(quantity) == percent

@pytest.mark.parametrize("quantity", [0, -1, 2.5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ----- parse_coupon -----
valid_codes = {
    "SAVE10": 10,
    "save25": 25,
    " SAVE50 ": 50,
}
for code, exp in valid_codes.items():
    def test_valid(code=code, exp=exp):
        assert cart.parse_coupon(code) == exp

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "1234", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ----- shipping_fee -----
@pytest.mark.parametrize("subtotal,member,fee", [
    (500, False, 60),
    (500, True, 30),
    (1000, False, 0),
    (1500, True, 0),
])
def test_shipping_fee(subtotal, member, fee):
    assert cart.shipping_fee(subtotal, member) == fee

@pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ----- Cart functionality -----
def test_cart_add_and_items():
    c = cart.Cart()
    assert c.items() == {}
    c.add_item("apple", 1.0, 3)
    assert c.items() == {"apple": 3}
    c.add_item("banana", 2.5)
    assert c.items() == {"apple": 3, "banana": 1}
    # adding same item increases quantity
    c.add_item("apple", 1.0, 2)
    assert c.items()["apple"] == 5
    # mismatched price raises ValueError
    with pytest.raises(ValueError):
        c.add_item("apple", 1.5, 1)

@pytest.mark.parametrize("quantity", [0, -1])
def test_cart_add_invalid(quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("pear", 3.0, quantity)

def test_cart_remove():
    c = cart.Cart()
    c.add_item("apple", 1.0, 5)
    c.remove_item("apple", 2)
    assert c.items()["apple"] == 3
    # remove more than existing removes item entirely
    c.remove_item("apple", 5)
    assert "apple" not in c.items()
    with pytest.raises(KeyError):
        c.remove_item("orange", 1)

# ----- subtotal calculation with bulk discounts -----
def test_subtotal_no_discount():
    c = cart.Cart()
    c.add_item("item", 10.0, 4)  # <10, no discount
    assert_close(c.subtotal(), 40.0)

def test_subtotal_with_discounts():
    c = cart.Cart()
    c.add_item("item", 20.0, 12)  # >10 => 5% off
    expected = 20.0 * 12 * 0.95
    assert_close(c.subtotal(), round(expected, 2))
    c.add_item("second", 30.0, 55)  # >=50 => 10% off
    expected += 30.0 * 55 * 0.90
    assert_close(c.subtotal(), round(expected, 2))

# ----- total calculation with coupon and shipping -----
def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("item", 100.0, 5)  # subtotal 500
    total_no_discount = 500 + 60  # member=False
    assert_close(c.total(member=False), round(total_no_discount, 2))
    # coupon SAVE10 reduces by 10%
    amount_after_coupon = 500 * 0.90
    shipping = cart.shipping_fee(amount_after_coupon)
    total_with_coupon = amount_after_coupon + shipping
    assert_close(c.total(member=False, coupon="SAVE10"), round(total_with_coupon, 2))
    # member gets half shipping
    shipping_member = cart.shipping_fee(amount_after_coupon, member=True)
    total_member = amount_after_coupon + shipping_member
    assert_close(c.total(member=True, coupon="SAVE10"), round(total_member, 2))

# ----- empty cart costs zero -----
def test_empty_cart_total():
    c = cart.Cart()
    assert c.subtotal() == 0
    assert c.total() == 0
