import pytest
from cart import Cart, apply_discount, parse_coupon, shipping_fee

# ---------- Test add_item and validation ----------

def test_add_positive_unit_price_and_quantity():
    c = Cart()
    c.add_item("apple", 0.5, quantity=3)
    assert c.items() == {"apple": 3}


def test_add_negative_unit_price_raises():
    c = Cart()
    with pytest.raises(ValueError):
        c.add_item("banana", -1.0)


def test_add_non_integer_quantity_raises():
    c = Cart()
    with pytest.raises(ValueError):
        c.add_item("pear", 1.5, quantity=2.3)


def test_add_zero_or_negative_quantity_raises():
    c = Cart()
    for q in [0, -2]:
        with pytest.raises(ValueError):
            c.add_item("grape", 1.0, quantity=q)


def test_reusing_existing_item_increases_quantity_and_enforces_unit_price():
    c = Cart()
    c.add_item("mango", 2.0, quantity=1)
    # same price: increase
    c.add_item("mango", 2.0, quantity=4)
    assert c.items() == {"mango": 5}
    # different price: error
    with pytest.raises(ValueError):
        c.add_item("mango", 3.0, quantity=1)

# ---------- Test remove_item behavior ----------

def test_remove_existing_quantity_and_removal_when_zero():
    c = Cart()
    c.add_item("cherry", 0.2, quantity=5)
    c.remove_item("cherry", quantity=3)
    assert c.items() == {"cherry": 2}
    c.remove_item("cherry", quantity=2)  # removes item completely
    assert "cherry" not in c.items()

def test_remove_more_than_exists_deletes_and_does_not_error_if_below_zero():
    c = Cart()
    c.add_item("melon", 1.0, quantity=2)
    c.remove_item("melon", quantity=5)  # should remove item
    assert "melon" not in c.items()


def test_remove_nonexistent_raises_key_error():
    c = Cart()
    with pytest.raises(KeyError):
        c.remove_item("orange")

# ---------- Test subtotal (basic calculation, discount abstracted) ----------

def test_subtotal_returns_round_to_two_decimals_and_zero_for_empty():
    c = Cart()
    assert c.subtotal() == 0.00
    c.add_item("bread", 1.2345, quantity=2)
    # no bulk discount assumed for simplicity
    assert c.subtotal() == round(1.2345 * 2, 2)

# ---------- Test parse_coupon specification ----------

def test_parse_valid_coupons_and_whitespace_case_insensitivity():
    for code in ["SAVE10", "save20", "  Save30  "]:
        assert parse_coupon(code) == int(code.strip()[4:])


def test_parse_invalid_coupons_raise_value_error():
    invalids = ["SA1VE10", "SAVEX0", "SAVE101", "foo", 123]
    for code in invalids:
        with pytest.raises(ValueError):
            parse_coupon(code)

# ---------- Test shipping_fee logic ----------

def test_shipping_fee_basic_and_member():
    import cart
    assert shipping_fee(1000) == 0
    assert shipping_fee(1001) == cart.SHIPPING_BASE
    assert shipping_fee(500, member=True) == cart.SHIPPING_BASE / 2
    with pytest.raises(ValueError):
        shipping_fee(-10)

# ---------- Test total calculation according to specification ----------

def test_total_empty_cart_no_shipping():
    c = Cart()
    assert c.total() == 0.00


def test_total_without_coupon_and_non_member_ships_based_on_subtotal():
    c = Cart()
    c.add_item("item", 100, quantity=3)  # subtotal 300
    import cart
    expected_shipping = shipping_fee(300)
    assert c.total() == round(300 + expected_shipping, 2)


def test_total_with_coupon_applies_discount_then_shipping():
    c = Cart()
    c.add_item("item", 200, quantity=5)  # subtotal 1000 - free shipping if no coupon
    # With a 10% coupon, amount after discount: 900, not free
    assert c.total(coupon="SAVE10") == round(900 + shipping_fee(900), 2)


def test_total_member_shipping_half_when_not_free():
    c = Cart()
    c.add_item("item", 200, quantity=3)  # subtotal 600
    import cart
    expected_shipping = shipping_fee(600, member=True)
    assert c.total(member=True) == round(600 + expected_shipping, 2)

# ---------- Test that invalid coupon raises ValueError in total ----------

def test_total_invalid_coupon_raises():
    c = Cart()
    c.add_item("item", 100, quantity=1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
