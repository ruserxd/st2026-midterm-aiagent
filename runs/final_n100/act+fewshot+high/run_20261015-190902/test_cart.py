import pytest
import cart

# --- apply_discount tests ---
@pytest.mark.parametrize("price, percent, expected", [
    (200, 15, 170.0),
    (99, 33, 66.33),
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected


def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        cart.apply_discount(-10, 20)

@pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# --- bulk_discount_percent tests ---
@pytest.mark.parametrize("quantity, expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),      # spec expects 10
    (51, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, "a"])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --- parse_coupon tests ---
@pytest.mark.parametrize("code, expected", [
    ("SAVE10", 10),
    ("save10", 10),          # case‑insensitive
    ("  SAVE20   ", 20),
    ("SaVe30", 30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["INVALID", "SAVE0", "SAVE51", None, 123, "save"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee tests ---
def test_shipping_fee_free_threshold():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0

@pytest.mark.parametrize("subtotal, member, expected", [
    (999.99, False, 60),
    (999.99, True, 30),
    (500,   False, 60),
    (500,   True,  30),
])
def test_shipping_fee_below_threshold(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

def test_shipping_fee_negative():
    with pytest.raises(ValueError):
        cart.shipping_fee(-1)

# --- Cart tests ---
def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item("Apple", 1.00, quantity=5)
    assert c.items() == {"Apple": 5}

def test_cart_add_duplicate_same_price():
    c = cart.Cart()
    c.add_item("Apple", 1.00, quantity=3)
    c.add_item("Apple", 1.00, quantity=2)
    assert c.items()["Apple"] == 5

def test_cart_add_price_mismatch():
    c = cart.Cart()
    c.add_item("Apple", 1.00, quantity=3)
    with pytest.raises(ValueError):
        c.add_item("Apple", 2.00)

@pytest.mark.parametrize("qty_to_remove, remaining", [
    (3, 2),
    (1, 4),
])
def test_cart_remove_partial_and_full(qty_to_remove, remaining):
    # Setup cart
    c = cart.Cart()
    c.add_item("Orange", 0.50, quantity=5)
    c.remove_item("Orange", qty_to_remove)
    if remaining > 0:
        assert c.items()["Orange"] == remaining
    else:
        assert "Orange" not in c.items()

def test_cart_remove_all_units():
    c = cart.Cart()
    c.add_item("Apple", 1.00, quantity=5)
    c.remove_item("Apple", 5)   # remove all
    assert "Apple" not in c.items()

def test_cart_remove_more_than_quantity():
    c = cart.Cart()
    c.add_item("Banana", 0.5, quantity=3)
    c.remove_item("Banana",4)   # more than existing
    assert "Banana" not in c.items()

def test_cart_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("Grapes")

# Subtotal tests
def test_cart_subtotal_simple():
    c = cart.Cart()
    c.add_item("A", 10.00, quantity=5)   # no discount
    c.add_item("B", 20.00, quantity=10)  # discount 5%
    expected = round(10*5 + 20*10*(1-0.05), 2)
    assert c.subtotal() == expected

def test_cart_subtotal_empty():
    c = cart.Cart()
    assert c.subtotal() == 0

def test_cart_subtotal_bulk_discount():
    c = cart.Cart()
    c.add_item("Expensive", 2.00, quantity=100)  # discount 15%
    expected_line_total = round(2.00*100*(1-0.15), 2)
    assert c.subtotal() == expected_line_total

# Total tests
def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0

def test_cart_total_no_coupon_non_member():
    c = cart.Cart()
    c.add_item("Item", 100.00, quantity=1)
    assert c.total() == 160          # 100 + 60
    assert c.total(member=True) == 130   # 100 + 30

def test_cart_total_with_coupon():
    c = cart.Cart()
    c.add_item("Item", 100.00, quantity=1)
    assert c.total(coupon="SAVE10") == 150     # 90 + 60

def test_cart_total_discount_below_threshold():
    c = cart.Cart()
    c.add_item("Expensive", 1100.00, quantity=1)
    # discounted subtotal becomes 990
    assert c.total(coupon="SAVE10") == 1050       # 990 + 60
    assert c.total(member=True, coupon="SAVE10") == 1020   # 990 + 30

def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("Item", 100.00)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
