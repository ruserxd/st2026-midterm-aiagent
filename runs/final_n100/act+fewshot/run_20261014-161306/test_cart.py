import pytest
import cart

# helper for float equality

def approx(val, expected):
    return abs(val - expected) < 1e-9

# --- apply_discount ---
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [(-1, 10), (10, -5), (10, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --- bulk_discount_percent ---
@pytest.mark.parametrize("qty,percent", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(qty, percent):
    assert cart.bulk_discount_percent(qty) == percent

@pytest.mark.parametrize("qty", [0, -5, 3.2])
def test_bulk_discount_percent_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# --- parse_coupon ---
@pytest.mark.parametrize("code,percent", [
    ("SAVE10", 10),
    ("save25 ", 25),
    (" SAVE5", 5),
])
def test_parse_coupon(code, percent):
    assert cart.parse_coupon(code) == percent

@pytest.mark.parametrize("code", ["SAVEX", "SAVE0", "SAVE51", "GOOD", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee ---
@pytest.mark.parametrize("subtotal,member,fee", [
    (0, False, 60),
    (500, True, 30),
    (1000, False, 0),
    (1500, True, 0),
])
def test_shipping_fee(subtotal, member, fee):
    assert cart.shipping_fee(subtotal, member) == fee

@pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --- Cart operations ---
@pytest.fixture
def empty_cart():
    return cart.Cart()

def test_add_item_new(empty_cart):
    c = empty_cart
    c.add_item("apple", 1.0, 3)
    assert c.items() == {"apple": 3}

def test_add_item_existing_same_price(empty_cart):
    c = empty_cart
    c.add_item("banana", 2.5, 2)
    c.add_item("banana", 2.5, 1)
    assert c.items() == {"banana": 3}

def test_add_item_existing_diff_price(empty_cart):
    c = empty_cart
    c.add_item("orange", 1.0, 1)
    with pytest.raises(ValueError):
        c.add_item("orange", 1.5, 1)

@pytest.mark.parametrize("name,qty", [("apple", -2), ("pear", 0)])
def test_add_item_invalid(name, qty, empty_cart):
    c = empty_cart
    with pytest.raises(ValueError):
        c.add_item(name, 1.0, qty)

# --- remove_item ---
def test_remove_partial(empty_cart):
    c = empty_cart
    c.add_item("mango", 3.0, 5)
    c.remove_item("mango", 2)
    assert c.items() == {"mango": 3}

def test_remove_to_zero_and_beyond(empty_cart):
    c = empty_cart
    c.add_item("peach", 2.0, 2)
    c.remove_item("peach", 2)  # should remove entirely
    assert "peach" not in c.items()
    with pytest.raises(KeyError):
        c.remove_item("peach", 1)

# --- subtotal calculations ---
def test_subtotal_with_bulk_discount(empty_cart):
    c = empty_cart
    c.add_item("apple", 1.0, 10)  # bulk discount 5%
    expected = 1.0 * 10 * (1 - 0.05)
    assert approx(c.subtotal(), round(expected, 2))

# --- total calculations ---
def test_total_no_coupon_no_member(empty_cart):
    c = empty_cart
    c.add_item("item", 200.0, 1)
    # subtotal=200, shipping fee=60, total=260
    assert approx(c.total(), 260.0)

def test_total_with_coupon_and_member(empty_cart):
    c = empty_cart
    c.add_item("item", 500.0, 1)
    # subtotal=500, coupon SAVE10 -> 450, shipping fee 30 (member), total 480
    assert approx(c.total(member=True, coupon="SAVE10"), 480.0)

# --- empty cart total should be 0 ---
def test_total_empty_cart(empty_cart):
    c = empty_cart
    assert c.total() == 0
