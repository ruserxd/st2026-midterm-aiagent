import pytest
import cart

# -----------------------------
# Utility helpers for the tests
# -----------------------------

def approx_equal(a, b, eps=1e-9):
    return abs(a - b) < eps

# ---------- Tests for standalone functions ----------

test_apply_discount_cases = [
    (200.0, 15, 170.0),
    (100.0, 0, 100.0),
    (50.5, 10, 45.45),  # rounded to two decimals
]

@pytest.mark.parametrize("price,percent,expected", test_apply_discount_cases)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == pytest.approx(expected)

# Invalid inputs for apply_discount
@pytest.mark.parametrize("price", [-10.0])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [ -5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100.0, percent)

# ---------- Tests for bulk_discount_percent ----------
bulk_cases = [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
]

@pytest.mark.parametrize("quantity,expected", bulk_cases)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# Invalid quantity
with pytest.raises(ValueError):
    cart.bulk_discount_percent(0)
with pytest.raises(ValueError):
    cart.bulk_discount_percent(-5)

# ---------- Tests for parse_coupon ----------
parse_cases = [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
]

@pytest.mark.parametrize("code,expected", parse_cases)
def test_parse_coupon(code, expected):
    assert cart.parse_coupon(code) == expected

# Invalid coupons
invalid_coupons = ["", "DISCOUNT10", "SAVE51", "save0", "sAvE101"]
for ic in invalid_coupons:
    with pytest.raises(ValueError):
        cart.parse_coupon(ic)

# ---------- Tests for shipping_fee ----------
shipping_cases = [
    (0, 60),          # non-member
    (999.99, 60),     # non-member just below free threshold
    (1000, 0),        # free shipping
    (1500, 0),
]

@pytest.mark.parametrize("subtotal,expected", shipping_cases)
def test_shipping_fee(subtotal, expected):
    assert cart.shipping_fee(subtotal) == expected

# Member discount
assert cart.shipping_fee(500, member=True) == 30

with pytest.raises(ValueError):
    cart.shipping_fee(-10)

# ---------- Tests for Cart class behavior ----------

def test_cart_initial_state():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 0.0

@pytest.mark.parametrize("name,unit_price,quantity", [
    ("apple",5,10),
])
def test_cart_add_and_subtotal(name, unit_price, quantity):
    c = cart.Cart()
    c.add_item(name, unit_price=unit_price, quantity=quantity)
    expected = unit_price * quantity * (1 - 0.05)  # 10 items => 5% bulk discount
    assert c.subtotal() == pytest.approx(expected)

# Adding same item with different price should raise ValueError

def test_cart_add_same_item_different_price():
    c = cart.Cart()
    c.add_item("apple", unit_price=5, quantity=5)
    with pytest.raises(ValueError):
        c.add_item("apple", unit_price=6, quantity=1)

# Removing items and checking removal when zero

def test_cart_remove_and_absence():
    c = cart.Cart()
    c.add_item("apple", unit_price=5, quantity=10)
    c.remove_item("apple", quantity=5)
    assert c.items() == {"apple": 5}
    c.remove_item("apple", quantity=5)
    # After removal the item should be absent
    assert "apple" not in c.items()
    with pytest.raises(KeyError):
        c.remove_item("banana")

# Cart total with coupon and shipping

def test_cart_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("book", unit_price=200, quantity=3)  # subtotal: 600
    amount_after_coupon = cart.apply_discount(600.0, 10)
    expected_total = round(amount_after_coupon + 60, 2)  # shipping 60
    assert c.total(coupon="SAVE10") == pytest.approx(expected_total)

# Member gets half shipping and discount applied to subtotal before shipping

def test_cart_member_shipping_and_discount():
    cm = cart.Cart()
    cm.add_item("gift", unit_price=2000, quantity=1)  # subtotal 2000 >1000 free shipping
    assert cm.total(member=True, coupon="SAVE20") == pytest.approx(1600.0)

# Invalid coupon should raise ValueError in total

def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("item", unit_price=100, quantity=1)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")

# Empty cart has zero cost, no shipping charged

def test_empty_cart_no_shipping():
    e = cart.Cart()
    assert e.total() == 0.0
