import pytest
import cart

# Helper for approximate equality

def approx_equal(a, b, eps=1e-6):
    return abs(a - b) < eps

# --- apply_discount tests ---
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [(-10, 5), (20, -1), (30, 110)])
def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --- bulk_discount_percent tests ---
@pytest.mark.parametrize("qty,expected", [
    (5, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (250, 15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -5, 2.5])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# --- parse_coupon tests ---
valid_codes = {
    "SAVE10": 10,
    "save20": 20,
    " SAVE5 ": 5,
    "SaVe50": 50,
}

@pytest.mark.parametrize("code,pct", list(valid_codes.items()))
def test_parse_coupon_valid(code, pct):
    assert cart.parse_coupon(code) == pct

invalid_codes = ["", "SAVEX", "SAVE0", "SAVE51", "XYZ10", " SAVE-5 "]

@pytest.mark.parametrize("code", invalid_codes)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee tests ---
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (500, True, 30),
    (999.99, False, 60),
    (1000, False, 0),
    (1500, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --- Cart functionality tests ---

def test_cart_initially_empty():
    c = cart.Cart()
    assert c.items() == []
    assert c.subtotal() == 0
    assert c.total() == 0


def test_add_and_remove_items():
    c = cart.Cart()
    c.add_item("apple", unit_price=100, quantity=3)
    c.add_item("banana", unit_price=50)
    # subtotal should be 3*100 + 1*50 = 350
    assert c.subtotal() == 350
    items = {i['name']: i for i in c.items()}
    assert items["apple"]["quantity"] == 3
    assert items["banana"]["quantity"] == 1

    c.remove_item("apple", quantity=2)
    items = {i['name']: i for i in c.items()}
    assert items["apple"]["quantity"] == 1
    assert c.subtotal() == 150

    with pytest.raises(ValueError):
        c.remove_item("banana", quantity=2)

# --- total calculation tests including coupon and shipping ---

def test_total_without_coupon_or_member():
    c = cart.Cart()
    c.add_item("item", unit_price=200, quantity=5)  # subtotal 1000
    assert c.total() == 1000.00


def test_total_with_coupon_and_member():
    c = cart.Cart()
    c.add_item("widget", unit_price=300, quantity=2)  # subtotal 600
    assert c.total(member=True, coupon="SAVE10") == pytest.approx(570.0)


def test_total_coupon_invalid_raises():
    c = cart.Cart()
    c.add_item("item", unit_price=100)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
