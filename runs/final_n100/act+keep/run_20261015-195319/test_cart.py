import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- simple function tests ----------

# apply_discount
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
    ],
)
def test_apply_discount_valid(price, percent, result):
    assert apply_discount(price, percent) == pytest.approx(result, rel=1e-9)

@pytest.mark.parametrize(
    "price,percent",
    [(-10, 20), (50, -5), (60, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# bulk_discount_percent
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (5, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (200, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 2.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# parse_coupon
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        (" save20 ", 20),
        ("SaVe5", 5),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "DISCOUNT10", "123", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# shipping_fee
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (500, True, 30),
        (1000, False, 0),
        (1500, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -50])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class tests ----------

# initialization and empty cart

def test_cart_empty():
    c = Cart()
    assert list(c.items().keys()) == []
    assert c.subtotal() == 0.0
    assert c.total() == 0.0

# adding items

def test_add_item_basic():
    c = Cart()
    c.add_item("apple", 1.00, 3)
    assert c.items() == {"apple": 3}
    # unit price same
    c.add_item("apple", 1.00, 2)
    assert c.items() == {"apple": 5}


def test_add_item_invalid_price_quantity():
    c = Cart()
    with pytest.raises(ValueError):
        c.add_item("banana", -1.0, 3)
    with pytest.raises(ValueError):
        c.add_item("banana", 1.0, 0)

# adding different item price conflict

def test_add_item_price_conflict():
    c = Cart()
    c.add_item("apple", 1.00, 2)
    with pytest.raises(ValueError):
        c.add_item("apple", 1.50, 1)

# removing items

def test_remove_item_basic_and_auto_remove():
    c = Cart()
    c.add_item("orange", 0.5, 4)
    c.remove_item("orange", 2)
    assert c.items() == {"orange": 2}
    c.remove_item("orange", 2)  # should remove completely
    assert c.items() == {}


def test_remove_nonexistent():
    c = Cart()
    with pytest.raises(KeyError):
        c.remove_item("pear", 1)

# subtotal calculation with bulk discounts

def test_subtotal_bulk_discount():
    c = Cart()
    # 5 items no discount
    c.add_item("itemA", 10.0, 5)
    # 12 items => 5% discount on those
    c.add_item("itemB", 20.0, 12)
    expected_subtotal = (
        10.0 * 5 +
        apply_discount(20.0 * 12, bulk_discount_percent(12))
    )
    assert c.subtotal() == pytest.approx(round(expected_subtotal, 2), rel=1e-9)

# total calculation with coupon and shipping

def test_total_with_coupon_and_shipping():
    c = Cart()
    c.add_item("item", 200.0, 5)  # no bulk discount
    subtotal = c.subtotal()  # should be 1000.0
    assert subtotal == 1000.0
    # coupon SAVE10 reduces by 10%
    total_with_coupon = c.total(coupon="SAVE10")
    expected_after_coupon = apply_discount(subtotal, 10)
    shipping = shipping_fee(expected_after_coupon, member=False)
    expected_total = round(expected_after_coupon + shipping, 2)
    assert total_with_coupon == expected_total

# empty cart no shipping

def test_total_empty_cart_no_shipping():
    c = Cart()
    assert c.total() == 0.0

# coupon invalid raises ValueError

def test_total_invalid_coupon():
    c = Cart()
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")

# member discount affects shipping fee

def test_shipping_fee_member_in_cart_total():
    c = Cart()
    c.add_item("heavy", 200.0, 3)  # 600 total
    subtotal = c.subtotal()
    assert subtotal == 600.0
    # as non-member: shipping 60
    total_nonmember = c.total(member=False)
    expected_nonmember = round(subtotal + shipping_fee(subtotal, False), 2)
    assert total_nonmember == expected_nonmember
    # as member: shipping 30
    total_member = c.total(member=True)
    expected_member = round(subtotal + shipping_fee(subtotal, True), 2)
    assert total_member == expected_member

# test bulk discount on large quantity in subtotal calculation

def test_subtotal_bulk_discount_edge_cases():
    c = Cart()
    # exactly 10 items -> 5%
    c.add_item("edge", 50.0, 10)
    assert c.subtotal() == pytest.approx(apply_discount(50.0 * 10, 5), rel=1e-9)
    # exactly 50 items -> 10%
    c = Cart()
    c.add_item("edge", 3.0, 50)
    assert c.subtotal() == pytest.approx(apply_discount(3.0 * 50, 10), rel=1e-9)
    # exactly 100 items -> 15%
    c = Cart()
    c.add_item("edge", 2.0, 100)
    assert c.subtotal() == pytest.approx(apply_discount(2.0 * 100, 15), rel=1e-9)
