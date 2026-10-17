import pytest
import cart

def assert_value_error(func, *args, **kwargs):
    with pytest.raises(ValueError):
        func(*args, **kwargs)

# apply_discount tests

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0


def test_apply_discount_errors():
    assert_value_error(cart.apply_discount, -10, 20)
    assert_value_error(cart.apply_discount, 100, -5)
    assert_value_error(cart.apply_discount, 100, 105)

# bulk_discount_percent tests

def test_bulk_discount_percent_levels():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 5
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

def test_bulk_discount_percent_errors():
    assert_value_error(cart.bulk_discount_percent, 0)
    assert_value_error(cart.bulk_discount_percent, -5)
    assert_value_error(cart.bulk_discount_percent, 3.5)

# parse_coupon tests

def test_parse_coupon_valid_cases():
    assert cart.parse_coupon("SAVE10") == 10
    # trailing space is invalid and should raise ValueError
    with pytest.raises(ValueError):
        cart.parse_coupon("save25 ")


def test_parse_coupon_invalid():
    for code in ["DISCOUNT", "SAVETEN", "SAVE", "SAVE0", "SAVE101"]:
        with pytest.raises(ValueError):
            cart.parse_coupon(code)

# shipping_fee tests

def test_shipping_fee_free():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500.5) == 0


def test_shipping_fee_non_member():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60


def test_shipping_fee_member_half():
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(999.99, member=True) == 30

# Cart tests

def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item("apple", 5)
    assert c.items() == {"apple": 1}
    c.add_item("apple", 5, quantity=2)
    assert c.items() == {"apple": 3}
    with pytest.raises(ValueError):
        c.add_item("apple", 4)


def test_cart_remove_item():
    c = cart.Cart()
    c.add_item("banana", 2, quantity=3)
    c.remove_item("banana")
    assert c.items() == {"banana": 2}
    c.remove_item("banana", quantity=2)
    # After removal quantity may be zero
    assert "banana" in c.items()
    assert c.items()["banana"] == 0
    c.add_item("cherry", 10, quantity=1)
    c.remove_item("cherry", quantity=5)
    assert "cherry" not in c.items()


def test_cart_subtotal():
    c = cart.Cart()
    c.add_item("apple", 1, quantity=4)
    assert c.subtotal() == 4.0
    c.add_item("orange", 2, quantity=10)
    expected_oranges = 20 * (1 - 0.05)
    assert c.subtotal() == round(4 + expected_oranges, 2)


def test_cart_total_no_coupon_non_member():
    c = cart.Cart()
    c.add_item("item", 1000)
    assert c.total(member=False) == 1000.0
    c.add_item("item2", 50)
    assert c.total(member=True) == 1050.0


def test_cart_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("item", 200, quantity=3)
    # subtotal 600, coupon 10% -> 540, shipping 60 non-member
    assert c.total(coupon="SAVE10") == 600.0
    # member gets half shipping: 30 + 540 = 570
    assert c.total(member=True, coupon="SAVE10") == 570.0


def test_cart_empty_total():
    c = cart.Cart()
    assert c.total() == 0
    assert c.total(coupon="SAVE10") == 0
