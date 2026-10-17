import pytest
import cart

def test_apply_discount_valid():
    # Basic discount
    assert cart.apply_discount(200, 15) == 170.0
    # Percent leading to a non‑integer result
    assert cart.apply_discount(100, 33) == 67.0

def test_apply_discount_errors():
    with pytest.raises(ValueError):
        cart.apply_discount(-5, 10)
    with pytest.raises(ValueError):
        cart.apply_discount(50, -1)
    with pytest.raises(ValueError):
        cart.apply_discount(50, 101)

def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    # Boundary value: should be 10 but implementation returns 5 due to > 50 check
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-3)

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    # case‑insensitive and whitespace trimmed
    assert cart.parse_coupon("   SaVe20   ") == 20
    # boundaries
    assert cart.parse_coupon("SAVE1") == 1
    assert cart.parse_coupon("SAVE50") == 50

def test_parse_coupon_invalid():
    with pytest.raises(ValueError):
        cart.parse_coupon("DISCOUNT10")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE0")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE51")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE-5")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVExx")
    with pytest.raises(ValueError):
        cart.parse_coupon("")
    with pytest.raises(ValueError):
        cart.parse_coupon("   ")

def test_shipping_fee():
    # Free shipping at or above 1000
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0
    # Non‑member fee
    assert cart.shipping_fee(500) == 60
    assert cart.shipping_fee(999.99) == 60
    # Member half fee
    assert cart.shipping_fee(500, member=True) == 30
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

def test_cart_initial_state():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

def test_cart_add_item():
    c = cart.Cart()
    # Add new item
    c.add_item("apple", 10.00, 2)
    assert c.items() == {"apple": 2}
    # Add same item with same price increases quantity
    c.add_item("apple", 10.00, 3)
    assert c.items() == {"apple": 5}
    # Adding different unit price raises error
    with pytest.raises(ValueError):
        c.add_item("apple", 12.00, 1)
    # Negative price or quantity raise ValueError
    with pytest.raises(ValueError):
        c.add_item("banana", -1, 2)
    with pytest.raises(ValueError):
        c.add_item("banana", 1, 0)

def test_cart_remove_item():
    c = cart.Cart()
    c.add_item("orange", 3.00, 4)
    # Remove part of quantity
    c.remove_item("orange", 2)
    assert c.items() == {"orange": 2}
    # Removing remaining quantity removes item entirely (bug: implementation keeps zero qty)
    c.remove_item("orange", 2)
    assert "orange" not in c.items()
    # Removing more than existing also results in removal
    c.add_item("kiwi", 1.00, 3)
    c.remove_item("kiwi", 5)
    assert "kiwi" not in c.items()
    # Removing nonexistent item raises KeyError
    with pytest.raises(KeyError):
        c.remove_item("nonexistent", 1)

def test_cart_items_copy():
    c = cart.Cart()
    c.add_item("mango", 2.00, 3)
    items_dict = c.items()
    assert items_dict == {"mango": 3}
    # Modify returned dict should not affect internal state
    items_dict["mango"] = 10
    assert c.items() == {"mango": 3}

def test_cart_subtotal():
    c = cart.Cart()
    # Item with no discount
    c.add_item("pen", 2.00, 5)      # qty=5 -> no bulk discount
    # Item with 5% discount (qty=12)
    c.add_item("notebook", 1.50, 12)
    # Item with 10% discount (qty=55)
    c.add_item("paper", 0.50, 55)
    expected = (
        2.00 * 5 +                     # 10
        1.50 * 12 * (1 - 0.05) +       # 1.50*12=18 -> minus 5% =>17.1
        0.50 * 55 * (1 - 0.10)         # 27.5 -> minus 10% =>24.75
    )
    expected = round(expected, 2)
    assert c.subtotal() == expected

def test_cart_total_no_coupon_and_membership():
    c = cart.Cart()
    c.add_item("pen", 2.00, 5)      # no bulk discount
    subtotal = c.subtotal()        # should be 10.0
    total_expected = round(subtotal + 60, 2)   # shipping fee for non‑member
    assert c.total(member=False) == total_expected

def test_cart_total_with_coupon_and_member():
    c = cart.Cart()
    c.add_item("pen", 2.00, 5)
    subtotal = c.subtotal()        # 10.0
    # Apply coupon of 10%
    amount_after_coupon = round(subtotal * (1 - 0.10), 2)   # 9.0
    total_expected = round(amount_after_coupon + 30, 2)     # member shipping half fee
    assert c.total(member=True, coupon="SAVE10") == total_expected

def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("pen", 1.00, 1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

def test_cart_total_empty_no_shipping():
    c = cart.Cart()
    assert c.total() == 0

# New test for shipping fee applied after coupon (spec requires this, but current implementation uses original subtotal)
def test_cart_total_shipping_after_coupon():
    c = cart.Cart()
    c.add_item("expensive", 500.00, 2)   # subtotal 1000
    assert c.total() == 1000  # no coupon, free shipping
    # Coupon reduces amount below threshold; expected shipping fee should apply
    assert c.total(coupon="SAVE10") == 960.0
