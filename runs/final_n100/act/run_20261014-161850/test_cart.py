import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount -------------------------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(100, 100) == 0.0

@ pytest.mark.parametrize(
    "price,percent",
    [(-1, 10), (50, -5), (50, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent -----------------------------------------

def test_bulk_discount_percent_levels():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(200) == 15

@ pytest.mark.parametrize("q", [0, -5, 3.2])
def test_bulk_discount_invalid(q):
    with pytest.raises(ValueError):
        bulk_discount_percent(int(q)) if isinstance(q, int) else bulk_discount_percent(q)

# ---------- parse_coupon ---------------------------------------------------

def test_parse_coupon_valid():
    for code in ["SAVE10", "save10", "  SAVE25 "]:
        assert parse_coupon(code) == 10 if code.strip().lower() == "save10" else 25

@ pytest.mark.parametrize("code", ["SAV10", "SAVE0", "SAVE51", "abc", "SAVE-5"]) 
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ---------------------------------------------------

def test_shipping_fee_free_and_half():
    assert shipping_fee(1000) == 0.0
    assert shipping_fee(999) == 60
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(1200, member=True) == 0

@ pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart tests -----------------------------------------------------

def test_cart_empty_total_and_subtotal():
    cart = Cart()
    assert cart.subtotal() == 0.0
    assert cart.total() == 0.0

@ pytest.mark.parametrize(
    "items,expected_subtotal",
    [([("apple", 100, 5)], 475),  # bulk discount 5% for 5 units -> 95 each
     ([("pear", 200, 10)], 1900 * (1 - 0.05)),  # 5% discount on 200*10=2000 => 1900
    ],
)
def test_cart_subtotal(items, expected_subtotal):
    cart = Cart()
    for name, price, qty in items:
        cart.add_item(name, price, qty)
    assert pytest.approx(cart.subtotal(), 2) == round(expected_subtotal, 2)

@ pytest.mark.parametrize(
    "items,coupon,member,expected_total",
    [
        ([("apple", 100, 5)], None, False, 475 + shipping_fee(475)),
        ([("apple", 100, 5)], "SAVE10", False, (475 * 0.9) + shipping_fee(475 * 0.9)),
        ([("pear", 200, 20)], "SAVE25", True, (4000 * 0.75) + shipping_fee(4000 * 0.75, member=True)),
    ],
)
def test_cart_total(items,coupon,member,expected_total):
    cart = Cart()
    for name, price, qty in items:
        cart.add_item(name, price, qty)
    assert pytest.approx(cart.total(member=member, coupon=coupon), 2) == round(expected_total, 2)

# ---------- add_item and remove_item validation ---------------------------

def test_add_item_errors():
    c = Cart()
    with pytest.raises(ValueError):
        c.add_item("book", -10, 1)
    with pytest.raises(ValueError):
        c.add_item("book", 20, 0)

    c.add_item("book", 20, 3)
    with pytest.raises(ValueError):
        c.add_item("book", 25, 2)  # price mismatch

@ pytest.mark.parametrize(
    "remove_sequence",
    [
        ([("pen", 5, 1)], [("pen", 0)]),  # remove all -> gone
        ([("pen", 5, 3)], [("pen", 2), ("pen", 1)]) ,  # reduces to zero
    ],
)
def test_remove_item(remove_sequence):
    c = Cart()
    for name, price, qty in remove_sequence[0]:
        c.add_item(name, price, qty)
    for name, qty in remove_sequence[1]:
        c.remove_item(name, qty)
    assert "pen" not in c.items()

@ pytest.mark.parametrize("name", ["nonexistent"])
def test_remove_nonexistent_raises(name):
    c = Cart()
    with pytest.raises(KeyError):
        c.remove_item(name, 1)

# ---------- items() returns copy -------------------------------------------------

def test_items_returns_copy():
    c = Cart()
    c.add_item("a", 10, 2)
    d = c.items()
    d["a"] = 5
    assert c.items()["a"] == 2
