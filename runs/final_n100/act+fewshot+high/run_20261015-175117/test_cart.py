import pytest
import cart

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(10, 33) == 6.7

def test_apply_discount_errors():
    with pytest.raises(ValueError):
        cart.apply_discount(-1, 10)
    with pytest.raises(ValueError):
        cart.apply_discount(10, -5)
    with pytest.raises(ValueError):
        cart.apply_discount(10, 105)

@pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),   # should be 10 per spec
    (51, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent_values(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 3.5])
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

def test_parse_coupon_valid_cases():
    assert cart.parse_coupon("SAVE10") == 10
    # Case‑insensitive codes should also work
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon(" SAVE30 ") == 30

@pytest.mark.parametrize("code", ["SAVEX", 123, "SAVE0", "SAVE51"])\n
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

def test_shipping_fee_threshold():
    # Free shipping when subtotal >= 1000
    assert cart.shipping_fee(1001) == 0
    # Normal fee for smaller subtotals
    assert cart.shipping_fee(999.99) == 60
    # Members pay half
    assert cart.shipping_fee(999.99, member=True) == 30

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

def test_add_item():
    c = cart.Cart()
    c.add_item("apple", 1.0, 3)
    assert c.items() == {"apple": 3}
    # Adding same item increments quantity
    c.add_item("apple", 1.0, 2)
    assert c.items() == {"apple": 5}
    # Different unit price should raise ValueError
    with pytest.raises(ValueError):
        c.add_item("apple", 1.5)

def test_remove_item():
    c = cart.Cart()
    c.add_item("banana", 0.5, 4)
    c.remove_item("banana", 2)
    assert c.items() == {"banana": 2}
    # Removing remaining quantity should delete the item entirely
    c.remove_item("banana", 2)
    assert "banana" not in c.items()

def test_remove_item_more_than_present():
    c = cart.Cart()
    c.add_item("pear", 1.0, 3)
    c.remove_item("pear", 5)   # should delete the item
    assert "pear" not in c.items()

def test_subtotal_with_bulk_discount():
    c = cart.Cart()
    c.add_item("X", 100.0, 10)  # bulk discount of 5%
    c.add_item("Y", 50.0, 4)   # no discount
    assert c.subtotal() == 1150.0

def test_total_shipping_fee_after_coupon_bug():
    c = cart.Cart()
    # Subtotal exactly 1000
    c.add_item("Z", 200.0, 5)
    amount_after_coupon = cart.apply_discount(1000, 10)   # 900
    expected_shipping = cart.shipping_fee(amount_after_coupon)
    expected_total = round(amount_after_coupon + expected_shipping, 2)
    assert c.total(coupon="SAVE10") == expected_total

def test_total_no_items():
    c = cart.Cart()
    assert c.total() == 0
