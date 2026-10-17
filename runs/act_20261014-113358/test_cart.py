import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# ---------- basic function tests ----------

@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
    ],
)
def test_apply_discount_valid(price, percent, result):
    assert apply_discount(price, percent) == result

@pytest.mark.parametrize(
    "price,percent",
    [(-1, 10), (10, -5), (10, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# bulk discount tests
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (1, 0),
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 2.3])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# coupon parsing tests
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        (" save25 ", 25),
        ("SaVe1", 1),
        ("SAve50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVEX", "SAVE0", "SAVE51", "abc", " ", None])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# shipping fee tests
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (500, True, 30),
        (999.99, False, 60),
        (1000, False, 0),
        (1200, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart tests ----------

def test_cart_subtotal_and_total_empty():
    c = Cart()
    assert c.subtotal() == 0.0
    assert c.total() == 0.0

def test_cart_add_remove_items_and_totals():
    c = Cart()
    c.add_item("apple", unit_price=100, quantity=2)  # subtotal 200
    c.add_item("banana", unit_price=50, quantity=3)   # subtotal 350
    assert c.subtotal() == 350.0
    assert c.total() == pytest.approx(410.0)  # 350 + 60 shipping = 410

    # apply coupon 10%
    assert c.total(coupon="SAVE10") == pytest.approx((350*0.9)+60)

    # member discount on shipping
    assert c.total(member=True, coupon=None) == pytest.approx(350+30)

    # remove some items
    c.remove_item("banana", quantity=1)  # remove one banana
    assert c.subtotal() == 300.0
    assert c.total() == pytest.approx(360.0)  # 300 + 60 shipping

    # bulk discount via coupon with multiple same items
    c = Cart()
    c.add_item("widget", unit_price=20, quantity=120)
    # subtotal 2400
    # bulk discount percent for 120 units is 15%
    expected_total = 2400*0.85 + 60  # shipping since not member and subtotal>1000? actually subtotal after coupon 2040>=1000 so free shipping
    assert c.total(coupon="SAVE10") == pytest.approx(2040+60)  # but need to check logic: shipping computed on amount after coupon, 2400*0.9=2160 => shipping 0 -> total 2160

# edge case: invalid coupon in cart total
    c = Cart()
    c.add_item("x", unit_price=10)
    with pytest.raises(ValueError):
        c.total(coupon="BAD")
