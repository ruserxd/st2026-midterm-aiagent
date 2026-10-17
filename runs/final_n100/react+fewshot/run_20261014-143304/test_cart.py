import pytest
import cart

# --- apply_discount ---
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [(-10, 20), (100, -5), (50, 110)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --- bulk_discount_percent ---
@pytest.mark.parametrize("quantity,expected", [
    (5, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 2.5, "10"])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --- parse_coupon ---
valid_coupons = {
    "SAVE10": 10,
    "save25": 25,
    "  SaVe5  ": 5,
}
@pytest.mark.parametrize("code,expected", list(valid_coupons.items()))
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

invalid_codes = ["DISCOUNT10", "SAVE0", "SAVE51", "SAVEX", "", "  "]
@pytest.mark.parametrize("code", invalid_codes)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee ---
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (999.99, False, 60),
    (1000, False, 0),
    (1500, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --- Cart class basics ---
def test_cart_initial_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0.0

# --- add_item and subtotal ---
def test_add_item_and_subtotal():
    c = cart.Cart()
    c.add_item("apple", 1.5, 3)
    c.add_item("banana", 0.8)
    assert c.items() == {"apple": 3, "banana": 1}
    assert pytest.approx(c.subtotal(), rel=1e-9) == 5.3

# --- add existing item same price ---
def test_add_existing_item_same_price():
    c = cart.Cart()
    c.add_item("apple", 2.0, 2)
    c.add_item("apple", 2.0, 1)
    assert c.items() == {"apple": 3}

# --- add existing item different price ---
def test_add_existing_item_different_price():
    c = cart.Cart()
    c.add_item("apple", 2.0)
    with pytest.raises(ValueError):
        c.add_item("apple", 3.0)

# --- remove_item tests ---
def test_remove_partial_and_removal():
    c = cart.Cart()
    c.add_item("apple", 1.0, 3)
    c.remove_item("apple", 1)
    assert c.items() == {"apple": 2}
    c.remove_item("apple", 2)
    assert c.items() == {}

def test_remove_nonexistent_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent")

# --- total calculations ---
def test_total_without_discounts():
    c = cart.Cart()
    c.add_item("item", 100, 5)  # subtotal 500
    assert pytest.approx(c.total(), rel=1e-9) == 560.0

def test_total_with_coupon_and_member_shipping():
    c = cart.Cart()
    c.add_item("item", 200, 10)  # subtotal 2000
    total = c.total(member=True, coupon="SAVE20")
    assert pytest.approx(total, rel=1e-9) == 1600.0

def test_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("item", 100, 1)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
