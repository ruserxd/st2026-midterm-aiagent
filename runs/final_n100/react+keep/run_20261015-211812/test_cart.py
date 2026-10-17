import pytest
import cart

def round2(value):
    return round(float(value), 2)

# --- function tests ---

test_cases_apply_discount = [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
]
@pytest.mark.parametrize("price,percent,expected", test_cases_apply_discount)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == pytest.approx(expected)

# invalid inputs
with pytest.raises(ValueError):
    cart.apply_discount(-10, 20)
with pytest.raises(ValueError):
    cart.apply_discount(100, -5)
with pytest.raises(ValueError):
    cart.apply_discount(100, 120)

# bulk_discount_percent cases
bulk_cases = [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
]
@pytest.mark.parametrize("qty,expected", bulk_cases)
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

with pytest.raises(ValueError):
    cart.bulk_discount_percent(0)
with pytest.raises(ValueError):
    cart.bulk_discount_percent(-5)

# parse_coupon tests
coupon_cases = [
    ("SAVE10", 10),
    ("save15 ", 15),
    (" SAVE20 ", 20),
]
@pytest.mark.parametrize("code,expected", coupon_cases)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

invalid_coupons = ["SAV10", "SAVE", "SAVE0", "SAVE51", "save-5", "foo"]
for code in invalid_coupons:
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
shipping_cases = [
    (999, 60),
    (1000, 0),
    (1500, 0),
]
@pytest.mark.parametrize("subtotal,expected", shipping_cases)
def test_shipping_fee(subtotal, expected):
    assert cart.shipping_fee(subtotal) == expected
# member half fee
assert cart.shipping_fee(800, member=True) == 30
with pytest.raises(ValueError):
    cart.shipping_fee(-5)

# --- Cart class tests ---

def test_add_and_subtotal_basic():
    c = cart.Cart()
    # quantity <10 so no bulk discount
    c.add_item("apple", 100, quantity=3)
    assert round2(c.subtotal()) == pytest.approx(300.0)


def test_add_same_item_with_diff_price():
    c = cart.Cart()
    c.add_item("banana", 50)
    with pytest.raises(ValueError):
        c.add_item("banana", 60)  # price mismatch


def test_remove_item_and_quantity():
    c = cart.Cart()
    c.add_item("orange", 30, quantity=5)
    c.remove_item("orange", quantity=2)
    assert c.items()["orange"] == 3
    c.remove_item("orange", quantity=3)  # quantity becomes 0 but key remains
    assert "orange" in c.items() and c.items()["orange"] == 0
    with pytest.raises(KeyError):
        c.remove_item("orange")


def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("widget", 200, quantity=1)
    subtotal = c.subtotal()
    amount_after_coupon = cart.apply_discount(subtotal, cart.parse_coupon("SAVE10"))
    shipping = cart.shipping_fee(amount_after_coupon) if not subtotal >= 1000 else 0
    expected_total = round2(amount_after_coupon + shipping)
    assert c.total(coupon="SAVE10") == pytest.approx(expected_total)


def test_total_no_items_returns_zero():
    c = cart.Cart()
    assert c.total() == 0

# Test that shipping in Cart.total uses subtotal AFTER coupon (spec)

def test_total_shipping_applied_after_coupon():
    c = cart.Cart()
    c.add_item("thing", 1000)
    # remove item but leave zero quantity bug
    c.remove_item("thing")
    c.add_item("small", 10)
    total_with_coupon = c.total(coupon="SAVE50")
    assert total_with_coupon == pytest.approx(65.0)

# Test member discount on shipping
c_member = cart.Cart()
c_member.add_item("gift", 20, quantity=50)  # bulk discount triggers 10%
amount_after_discount = c_member.subtotal() * 0.90  # apply 10% coupon
expected_total = round2(amount_after_discount + cart.shipping_fee(amount_after_discount, member=True))
assert c_member.total(member=True, coupon="SAVE10") == pytest.approx(expected_total)
