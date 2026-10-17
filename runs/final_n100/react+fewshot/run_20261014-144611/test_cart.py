import pytest
import cart

# ---------- Utility helpers for expected calculations ----------

def expect_apply_discount(price, percent):
    return round(price * (1 - percent / 100), 2)

# ---------- Tests for individual helper functions ----------

def test_apply_discount_basic():
    assert cart.apply_discount(200.0, 15) == 170.0

@ pytest.mark.parametrize(
    "price,percent,expected",
    [
        (100.0, 0, 100.0),
        (50.5, 10, round(50.5 * 0.90, 2)),
        (120, 100, 0.0),
    ],
)
def test_apply_discount_various(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@ pytest.mark.parametrize("price", [ -1, -10 ])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 20)

@ pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(50, percent)

# ---------- Bulk discount tests ----------

def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

@ pytest.mark.parametrize("quantity", [0, -1])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- Coupon parsing tests ----------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon(" save20 ") == 20
    assert cart.parse_coupon("SaVe1") == 1

@ pytest.mark.parametrize("code", ["SAve51", "discount", "save0", "save-5"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- Shipping fee tests ----------

def test_shipping_fee():
    assert cart.shipping_fee(999) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0

@ pytest.mark.parametrize("subtotal", [ -1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class tests ----------

def test_cart_initial_state():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 0.0


def test_add_and_remove_items():
    c = cart.Cart()
    c.add_item("apple", 5, 2)
    assert c.items() == {"apple": 2}
    c.add_item("apple", 5, 3)  # same price, quantity increases
    assert c.items() == {"apple": 5}

    with pytest.raises(ValueError):
        c.add_item("banana", -1)

    with pytest.raises(ValueError):
        c.add_item("orange", 2, 0)

    # removing items
    c.remove_item("apple", 3)
    assert c.items() == {"apple": 2}
    c.remove_item("apple", 2)  # quantity reaches zero -> removed
    assert c.items() == {}

    with pytest.raises(KeyError):
        c.remove_item("pear")

# ---------- Subtotal calculation test (bulk discount applied) ----------

def test_subtotal_with_bulk_discount():
    c = cart.Cart()
    c.add_item("widget", 10.0, 10)   # 5% bulk discount for 10 units
    expected = round(10.0 * 10 * (1 - 0.05), 2)
    assert c.subtotal() == expected

# ---------- Total calculation tests (coupon and shipping) ----------

def test_total_no_coupon_no_member():
    c = cart.Cart()
    c.add_item("book", 30, 3)  # no bulk discount
    # subtotal 90, coupon none => 90, shipping 60 -> total 150
    assert c.total() == round(90 + 60, 2)

def test_total_with_coupon():
    c = cart.Cart()
    c.add_item("pen", 10, 5)  # no bulk discount
    # subtotal 50, coupon SAVE10 reduces to 45, shipping 60 -> total 105
    assert c.total(coupon="SAVE10") == round(45 + 60, 2)

def test_total_member_shipping_half():
    c = cart.Cart()
    c.add_item("toy", 200, 1)  # subtotal 200
    # coupon none -> 200, shipping 60 (non member), but member pays half 30 => total 230
    assert c.total(member=True) == round(200 + 30, 2)

def test_total_shipping_free_when_subtotal_above_1000():
    c = cart.Cart()
    c.add_item("laptop", 1200, 1)
    # subtotal 1200 > 1000 => shipping free
    assert c.total() == round(1200, 2)

# ---------- Empty cart edge case (no shipping) ----------

def test_empty_cart_no_shipping():
    c = cart.Cart()
    assert c.total() == 0.0
