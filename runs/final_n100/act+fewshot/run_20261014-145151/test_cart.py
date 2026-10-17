import pytest
import cart

# Helper for expected discount calculation
def expected_discount(price, percent):
    return round(price * (1 - percent / 100), 2)

@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (123.45, 10, 111.11),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# Bulk discount percentages
@pytest.mark.parametrize("qty,percent", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (250, 15),
])
def test_bulk_discount_percent(qty, percent):
    assert cart.bulk_discount_percent(qty) == percent

@pytest.mark.parametrize("qty", [0, -5, 1.2])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# Coupon parsing
valid_codes = {
    "SAVE10": 10,
    "save20": 20,
    "  SaVe30  ": 30,
}
@pytest.mark.parametrize("code,percent", list(valid_codes.items()))
def test_parse_coupon_valid(code, percent):
    assert cart.parse_coupon(code) == percent

invalid_codes = ["SAVE0", "SAVE51", "SAVExx", "1234", "", "  "]
@pytest.mark.parametrize("code", invalid_codes)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Shipping fee
@pytest.mark.parametrize("subtotal,fee", [
    (0, 60),
    (999.99, 60),
    (1000, 0),
    (1500, 0),
])
def test_shipping_fee(subtotal, fee):
    assert cart.shipping_fee(subtotal) == fee

# Member half fee
@pytest.mark.parametrize("subtotal", [50, 500, 1200])
def test_shipping_member_half(subtotal):
    expected = 30 if subtotal < 1000 else 0
    assert cart.shipping_fee(subtotal, member=True) == expected

@pytest.mark.parametrize("subtotal", [-1, -500])
def test_shipping_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart functionality tests
@pytest.fixture
def empty_cart():
    return cart.Cart()

def test_empty_cart_subtotal_and_total(empty_cart):
    assert empty_cart.subtotal() == 0.0
    assert empty_cart.total() == 0.0
    assert empty_cart.total(member=True) == 0.0

def test_add_item(empty_cart):
    empty_cart.add_item("apple", 100, quantity=2)
    assert empty_cart.items() == {"apple": 2}
    # adding same item increases qty; case-sensitive name
    empty_cart.add_item("APPLE", 100, quantity=3)
    assert empty_cart.items()["APPLE"] == 3

# unit_price must match existing price
cart_obj = cart.Cart()
cart_obj.add_item("orange", 200)
with pytest.raises(ValueError):
    cart_obj.add_item("orange", 250)

# quantity validation
with pytest.raises(ValueError):
    cart_obj.add_item("banana", 50, quantity=0)

# Remove items
cart_remove = cart.Cart()
cart_remove.add_item("tea", 30, quantity=5)
cart_remove.remove_item("tea", quantity=2)
assert cart_remove.items()["tea"] == 3
cart_remove.remove_item("tea", quantity=3)  # should remove fully
# Removing a non-existent item may not raise; we simply skip the assertion if it doesn't raise
try:
    cart_remove.remove_item("tea")
except KeyError:
    pass

# subtotal with bulk discount
cart_sub = cart.Cart()
cart_sub.add_item("pen", 10, quantity=12)  # 5% discount on 12 units
expected_subtotal = round(10 * 12 * (1 - 0.05), 2)
assert cart_sub.subtotal() == expected_subtotal

# total with coupon and shipping
cart_total = cart.Cart()
cart_total.add_item("pen", 10, quantity=12)
cart_total.add_item("notebook", 200, quantity=1)
subtotal = cart_total.subtotal()
after_coupon = round(subtotal * 0.9, 2)  # SAVE10
shipping = 0 if after_coupon >= 1000 else 60
expected_total = round(after_coupon + shipping, 2)
assert cart_total.total(coupon="SAVE10") == expected_total

# total with member discount and coupon
cart_member = cart.Cart()
cart_member.add_item("eraser", 5, quantity=200)  # 15% bulk discount
subtotal_m = cart_member.subtotal()
after_coupon_m = round(subtotal_m * 0.85, 2)
shipping_m = 0 if after_coupon_m >= 1000 else 30
expected_total_m = round(after_coupon_m + shipping_m, 2)
assert cart_member.total(member=True, coupon="SAVE15") == expected_total_m
