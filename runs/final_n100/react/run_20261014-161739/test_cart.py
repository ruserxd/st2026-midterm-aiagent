import re
import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount tests ----------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize(
    "price, percent",
    [(-1, 10), (100, -5), (100, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent tests ----------

def test_bulk_discount_percent_brackets():
    assert bulk_discount_percent(5) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

def test_bulk_discount_percent_invalid():
    for bad in [0, -1, 3.5]:
        with pytest.raises(ValueError):
            bulk_discount_percent(bad)

# ---------- parse_coupon tests ----------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20") == 20
    assert parse_coupon(" SAVE30 ") == 30

@ pytest.mark.parametrize(
    "code",
    ["", "SAVEX", "SAVETOOLOW", "SAVE0", "SAVE51", "BAD10", "12345", "SAVELARGE"],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee tests ----------

def test_shipping_fee_basic():
    assert shipping_fee(1200) == 0
    assert shipping_fee(999.99) == 60
    assert shipping_fee(0) == 60

@ pytest.mark.parametrize(
    "subtotal",
    [-10, -1],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart tests ----------

def test_cart_add_and_remove():
    cart = Cart()
    assert cart.items() == {}
    cart.add_item("apple", 5.0, quantity=3)
    assert cart.items()["apple"] == (5.0, 3)

    # adding same item increases quantity
    cart.add_item("apple", 5.0, quantity=2)
    assert cart.items()["apple"] == (5.0, 5)

    # remove partially
    cart.remove_item("apple", quantity=2)
    assert cart.items()["apple"] == (5.0, 3)

    # remove more than exists -> should raise ValueError
    with pytest.raises(ValueError):
        cart.remove_item("apple", quantity=10)

    # removing nonexistent item raises
    with pytest.raises(KeyError):
        cart.remove_item("banana")

# subtotal calculation

def test_cart_subtotal():
    cart = Cart()
    cart.add_item("a", 2.5, quantity=4)  # 10
    cart.add_item("b", 3.0, quantity=2)  # 6
    assert cart.subtotal() == 16.0

# total calculation with discount and shipping

def test_cart_total_with_member_and_coupon():
    cart = Cart()
    cart.add_item("item", 200.0, quantity=5)  # subtotal 1000
    # bulk discount: 15% -> 850
    # coupon SAVE10 gives 10% on discounted amount -> 765
    # shipping free for subtotal >=1000 before discounts
    total = cart.total(member=True, coupon="SAVE10")
    assert pytest.approx(total, 1e-2) == 765.0

# total with nonmember and no coupon

def test_cart_total_nonmember_no_coupon():
    cart = Cart()
    cart.add_item("item", 200.0, quantity=5)
    # subtotal 1000 -> shipping free, bulk discount applied
    assert cart.total() == pytest.approx(850.0, rel=1e-9)

# total when subtotal below free threshold

def test_cart_total_nonmember_with_shipping():
    cart = Cart()
    cart.add_item("item", 50.0, quantity=5)  # 250
    # bulk discount: 0% for <10, so subtotal remains 250
    # shipping fee non-member: 60
    assert cart.total() == pytest.approx(310.0)

# coupon parsing in total

def test_cart_total_with_coupon_invalid_code():
    cart = Cart()
    cart.add_item("item", 10, quantity=1)
    with pytest.raises(ValueError):
        cart.total(coupon="WRONGCODE")
