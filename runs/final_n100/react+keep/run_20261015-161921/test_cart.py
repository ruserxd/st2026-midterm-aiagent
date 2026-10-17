import pytest
import cart

# ----- Helper functions -----

# expected round helper
round2 = lambda x: round(x, 2)

# ----- Tests for simple functions -----

def test_apply_discount_valid_cases():
    assert cart.apply_discount(200, 15) == 170.0
    # no discount
    assert cart.apply_discount(100, 0) == 100.0
    # full discount
    assert cart.apply_discount(50, 100) == 0.0


def test_apply_discount_invalid_values():
    with pytest.raises(ValueError):
        cart.apply_discount(-10, 20)
    with pytest.raises(ValueError):
        cart.apply_discount(10, -5)
    with pytest.raises(ValueError):
        cart.apply_discount(10, 150)


def test_bulk_discount_percent_thresholds():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(25) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(75) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15


def test_bulk_discount_invalid_quantity():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-5)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(3.5)  # not an int


def test_parse_coupon_valid_cases():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon(" SAVE30 ") == 30


def test_parse_coupon_invalid_cases():
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVEXY")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE101")
    with pytest.raises(ValueError):
        cart.parse_coupon("10SAVE")


def test_shipping_fee_cases():
    # free shipping
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500.75) == 0
    # regular fee
    assert cart.shipping_fee(500) == 60
    assert cart.shipping_fee(999.99) == 60
    # half for member
    assert cart.shipping_fee(300, member=True) == 30


def test_shipping_fee_invalid_subtotal():
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

# ----- Tests for Cart class -----

def test_cart_initial_state():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0


def test_add_item_basic_and_reuse():
    c = cart.Cart()
    c.add_item("apple", 1.00)
    assert c.items()["apple"] == 1
    assert c.subtotal() == 1.0
    # adding same item increases quantity
    c.add_item("apple", 1.00, 2)
    assert c.items()["apple"] == 3
    assert c.subtotal() == 3.0
    # unit price must match existing
    with pytest.raises(ValueError):
        c.add_item("apple", 1.50)


def test_add_item_invalid_values():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("banana", -0.5)
    with pytest.raises(ValueError):
        c.add_item("banana", 0.5, 0)
    with pytest.raises(ValueError):
        c.add_item("banana", 0.5, -3)


def test_remove_item_basic_and_deletion():
    c = cart.Cart()
    c.add_item("orange", 2.00, 5)
    # remove some quantity
    c.remove_item("orange", 3)
    assert c.items()["orange"] == 2
    assert c.subtotal() == 4.0
    # removing more than remaining should delete the item
    c.remove_item("orange", 2)
    assert "orange" not in c.items()
    # attempting to remove non-existent raises KeyError
    with pytest.raises(KeyError):
        c.remove_item("nonexistent")


def test_remove_item_zero_quantity_behavior_bug():
    # According to spec, removing enough should delete the item.
    c = cart.Cart()
    c.add_item("grape", 3.00, 2)
    c.remove_item("grape", 2)  # should remove the item entirely
    assert "grape" not in c.items()  # expect failure if implementation keeps zero


def test_cart_total_with_coupon_and_member():
    c = cart.Cart()
    c.add_item("item", 100.0, 10)  # bulk discount 5% => line total 950
    # subtotal: 950 * (1-0.05)=902.5 -> round to 902.5
    assert c.subtotal() == 902.5
    # no coupon, member True: shipping half of 60 =30, total=932.5
    assert c.total(member=True) == 932.5
    # add a valid coupon 10%
    assert c.total(coupon="SAVE10") == round(902.5 * 0.9 + cart.shipping_fee(902.5), 2)
    # invalid coupon should raise ValueError
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# ----- Edge case: subtotal over shipping threshold after discount -----

def test_total_shipping_free_after_discount():
    c = cart.Cart()
    c.add_item("expensive", 1000.0, 1)
    # subtotal before coupon = 1000, shipping free regardless of member or coupon
    assert c.total(member=True) == 1000.0
    assert c.total(coupon="SAVE50") == round(500.0 + cart.shipping_fee(cart.subtotal()), 2)
    # shipping fee should be based on amount after coupon
    # subtotal 1000, coupon 50% => 500, shipping free because >=1000? actually shipping free only if subtotal >=1000; spec uses subtotal before shipping.
    # In this case shipping fee is still free since amount >=1000 after discount
    assert cart.shipping_fee(500) == 60  # shipping would be 60 normally but code uses subtotal, so this test checks for mismatch
