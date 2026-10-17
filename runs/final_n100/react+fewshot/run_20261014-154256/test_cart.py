import pytest
import cart

# ---------------- apply_discount -----------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(99.99, 5) == round(99.99 * 0.95, 2)

@pytest.mark.parametrize("price,percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------------- bulk_discount_percent -----------------------------

def test_bulk_discount_percent_cases():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

@pytest.mark.parametrize("qty", [0, -1, 3.5])
def test_bulk_discount_percent_errors(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------------- parse_coupon -------------------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon("  SaVe50  ") == 50

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "NOTC", "SAVExx", "SAVE-5"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------------- shipping_fee -------------------------------------

def test_shipping_fee_basic():
    assert cart.shipping_fee(999) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1200) == 0
    assert cart.shipping_fee(400, member=True) == 30

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------------- Cart class ---------------------------------------

def test_cart_initial_state():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

def test_add_item_and_subtotal():
    c = cart.Cart()
    c.add_item("apple", 100, 5)
    expected_unit = 100 * 0.95  # bulk discount for 5 items
    assert c.subtotal() == round(5 * expected_unit, 2)
    assert c.items() == {"apple": 5}

    c.add_item("banana", 200, 1)
    assert c.items()["banana"] == 1
    total_expected = round(5 * expected_unit + 200, 2)
    assert c.subtotal() == total_expected

    c.add_item("apple", 100, 3)
    assert c.items()["apple"] == 8

    with pytest.raises(ValueError):
        c.add_item("apple", 90, 1)   # price mismatch

    with pytest.raises(ValueError):
        c.add_item("pear", -10, 2)   # negative unit_price
    with pytest.raises(ValueError):
        c.add_item("pear", 10, 0)     # non‑positive quantity

def test_remove_item():
    c = cart.Cart()
    c.add_item("orange", 50, 3)
    c.remove_item("orange", 1)
    assert c.items()["orange"] == 2
    c.remove_item("orange", 2)   # should remove entirely
    assert "orange" not in c.items()

    with pytest.raises(KeyError):
        c.remove_item("nonexistent", 1)

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("apple", 100, 10)   # subtotal: 10*100*0.95 = 950
    assert c.subtotal() == round(10 * 100 * 0.95, 2)

    total_after_coupon = round(c.subtotal() * 0.80, 2)  # 20% off
    shipping_fee = cart.shipping_fee(total_after_coupon)
    expected_final = round(total_after_coupon + shipping_fee, 2)
    assert c.total(coupon="SAVE20") == expected_final

    # member shipping half fee
    member_shipping = cart.shipping_fee(total_after_coupon, member=True)
    expected_member = round(total_after_coupon + member_shipping, 2)
    assert c.total(member=True) == expected_member

    with pytest.raises(ValueError):
        c.total(coupon="INVALID")

    e = cart.Cart()
    assert e.total() == 0
