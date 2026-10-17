import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# ---------- apply_discount ----------
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
        (99.999, 10, round(99.999*0.9,2)),
    ],
)
def test_apply_discount(price, percent, expected):
    assert apply_discount(price, percent) == pytest.approx(expected)

@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_invalid_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize(
    "qty,expected",
    [
        (0, None),
        (5, 0),
        (10, 5),
        (50, 10),
        (100, 15),
    ],
)
def test_bulk_discount_percent(qty, expected):
    if qty <= 0:
        with pytest.raises(ValueError):
            bulk_discount_percent(qty)
    else:
        assert bulk_discount_percent(qty) == expected

# ---------- parse_coupon ----------
valid_codes = {
    "SAVE10": 10,
    "save15": 15,
    " SAVE5 ": 5,
}
@pytest.mark.parametrize("code,exp", valid_codes.items())
def test_parse_coupon_valid(code, exp):
    assert parse_coupon(code) == exp

invalid_codes = ["", "SAV10", "SAVE51", "save0", "10SAVE", "SAVe-5"]
@pytest.mark.parametrize("code", invalid_codes)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (999.99, True, 30),
        (1000, False, 0),
        (1200, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

# ---------- Cart behavior ----------

def test_cart_add_and_items():
    c = Cart()
    c.add_item("apple", 1.0, 3)
    c.add_item("banana", 0.5, 2)
    assert c.items() == {"apple": 3, "banana": 2}

c = Cart()
c.add_item("apple", 1.0, 2)
c.add_item("apple", 1.0, 3)
assert c.items()["apple"] == 5
with pytest.raises(ValueError):
    c.add_item("apple", 1.5, 1)

c.remove_item("apple", 2)
assert c.items()["apple"] == 3
# Removing more than current quantity should delete item entirely
c.remove_item("apple", 10)
with pytest.raises(KeyError):
    c.remove_item("apple")

c = Cart()
c.add_item("widget", 100.0, 5)   # quantity 5 - no bulk discount
subtotal_expected = round(100*5,2)
assert c.subtotal() == subtotal_expected
amount_after_coupon = apply_discount(subtotal_expected, parse_coupon("SAVE10"))
expected_total_non_member = round(amount_after_coupon + shipping_fee(amount_after_coupon, member=False),2)
actual_total_non_member = c.total(member=False, coupon="SAVE10")
assert actual_total_non_member == expected_total_non_member
# Test scenario where discount drops below free shipping threshold
c = Cart()
c.add_item("widget", 150.0, 10)   # bulk discount 5% -> subtotal 1425
subtotal_expected = round(150*10*0.95,2)
assert c.subtotal() == subtotal_expected
amount_after_coupon = apply_discount(subtotal_expected, parse_coupon("SAVE40"))
# After 40% discount: 852 (<1000) shipping should be 60 non-member
expected_total_non_member = round(amount_after_coupon + shipping_fee(amount_after_coupon, member=False),2)
actual_total_non_member = c.total(member=False, coupon="SAVE40")
assert actual_total_non_member == expected_total_non_member
# If code used original subtotal for fee, total would be 852+0=852
total_if_original = round(amount_after_coupon + shipping_fee(subtotal_expected, member=False),2)
assert actual_total_non_member != total_if_original

empty = Cart()
assert empty.total() == 0
