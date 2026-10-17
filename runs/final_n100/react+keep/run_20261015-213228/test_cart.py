import pytest
import cart

# ---------- apply_discount ----------------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0


def test_apply_discount_zero_percent_and_price():
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(0, 50) == 0.0


def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        cart.apply_discount(-10, 20)


def test_apply_discount_invalid_percent():
    for bad in (-1, 101):
        with pytest.raises(ValueError):
            cart.apply_discount(100, bad)

# ---------- bulk_discount_percent ---------------------------------

def test_bulk_discount_thresholds():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

def test_bulk_discount_invalid_quantity():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-5)

# ---------- parse_coupon -------------------------------------------

def test_parse_coupon_valid_codes():
    # valid codes including whitespace and case variations
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save25 ") == 25
    assert cart.parse_coupon("   sAvE1") == 1
    assert cart.parse_coupon("   SAVE50  ") == 50

def test_parse_coupon_invalid_codes():
    invalids = ["", "SAV10", "SAVE0", "SAVE51", "DISCOUNT", "SAVE-5"]
    for code in invalids:
        with pytest.raises(ValueError):
            cart.parse_coupon(code)

# ---------- shipping_fee -------------------------------------------

def test_shipping_fee_basic():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(500) == 60
    assert cart.shipping_fee(999.99) == 60


def test_shipping_fee_free_for_over_1000():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0


def test_shipping_fee_member_half():
    assert cart.shipping_fee(200, member=True) == 30


def test_shipping_fee_invalid_subtotal():
    with pytest.raises(ValueError):
        cart.shipping_fee(-5)

# ---------- Cart class ---------------------------------------------

def test_cart_initial_state():
    c = cart.Cart()
    # Items should be empty structure; accept list or dict depending on implementation
    assert isinstance(c.items(), (list, dict))


def test_cart_add_and_subtotal_single_item():
    c = cart.Cart()
    c.add_item("Apple", unit_price=50, quantity=3)
    assert c.subtotal() == 150


def test_cart_add_existing_item_increases_quantity():
    c = cart.Cart()
    c.add_item("Banana", unit_price=30, quantity=2)
    c.add_item("Banana", unit_price=30, quantity=3)
    assert c.subtotal() == 150


def test_cart_remove_items_and_subtotal():
    c = cart.Cart()
    c.add_item("Carrot", unit_price=20, quantity=5)
    c.remove_item("Carrot", quantity=2)
    assert c.subtotal() == 60
    # Removing more than exists should remove the item entirely if implementation allows
    c.remove_item("Carrot", quantity=10)
    assert c.subtotal() == 0


def test_cart_total_with_coupon_and_member():
    c = cart.Cart()
    c.add_item("Item1", unit_price=200, quantity=1)  # subtotal 200
    total = c.total(member=True, coupon="SAVE10")
    # Apply 10% discount to 200 - 180; add shipping fee half of 60 => 30; expected 210
    assert total == pytest.approx(210)


def test_cart_total_without_coupon_and_non_member():
    c = cart.Cart()
    c.add_item("Item2", unit_price=1200, quantity=1)  # subtotal >=1000, free shipping
    assert c.total() == 1200


def test_cart_total_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item("Thing", unit_price=100, quantity=1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# ---------- Edge cases and error handling --------------------------

def test_cart_add_negative_quantity():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("Neg", unit_price=10, quantity=-1)


def test_cart_remove_nonexistent_item_raises_keyerror():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("NonExistent", quantity=1)
