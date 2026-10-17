import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# --- apply_discount -------------------------------------------------

def test_apply_discount_valid_cases():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(50, 100) == 0.0
    # rounding to two decimals
    assert apply_discount(99.999, 10) == round(89.9991, 2)

@pytest.mark.parametrize("price", [-1, -5])
def test_apply_discount_price_negative(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-1, 101, 150])
def test_apply_discount_percent_out_of_range(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# --- bulk_discount_percent -------------------------------------------

def test_bulk_discount_percent_cases():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@pytest.mark.parametrize("qty", [0, -5])
def test_bulk_discount_percent_invalid_qty(qty):
    with pytest.raises(ValueError):
        bulk_discount_percent(qty)

# --- parse_coupon ---------------------------------------------------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon(" save20 ") == 20
    assert parse_coupon("SaVe50") == 50

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "SAVExx", "DISCOUNT5", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# --- shipping_fee ---------------------------------------------------

def test_shipping_fee_standard():
    assert shipping_fee(0) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500) == 0

# member half fee
assert shipping_fee(500, member=True) == 30

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# --- Cart class -----------------------------------------------------

def test_cart_initial_empty():
    c = Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0.0


def test_add_item_new_and_existing():
    c = Cart()
    c.add_item("apple", 1.00, quantity=3)
    assert c.items() == {"apple": 3}
    # Adding same item with same unit price increases quantity
    c.add_item("apple", 1.00, quantity=2)
    assert c.items() == {"apple": 5}

    # Adding new item
    c.add_item("banana", 0.50)
    assert c.items() == {"apple": 5, "banana": 1}


def test_add_item_invalid_price_and_quantity():
    c = Cart()
    with pytest.raises(ValueError):
        c.add_item("orange", -1.00)
    with pytest.raises(ValueError):
        c.add_item("orange", 1.00, quantity=0)


def test_add_item_price_mismatch():
    c = Cart()
    c.add_item("pear", 2.00)
    with pytest.raises(ValueError):
        c.add_item("pear", 3.00)


def test_remove_item_partial_and_complete():
    c = Cart()
    c.add_item("item", 10, quantity=5)
    # remove fewer than existing
    c.remove_item("item", quantity=2)
    assert c.items() == {"item": 3}
    # remove remaining to zero
    c.remove_item("item", quantity=3)
    assert c.items() == {}


def test_remove_item_not_in_cart():
    c = Cart()
    with pytest.raises(KeyError):
        c.remove_item("ghost")


def test_subtotal_and_total_no_coupon_member():
    c = Cart()
    c.add_item("tshirt", 20, quantity=2)   # subtotal 40
    assert c.subtotal() == 40
    # no coupon, non-member shipping: subtotal <1000 => fee 60
    assert c.total(member=False, coupon=None) == round(40 + 60, 2)
    # member gets half fee
    assert c.total(member=True, coupon=None) == round(40 + 30, 2)


def test_total_with_coupon_and_shipping():
    c = Cart()
    c.add_item("book", 100, quantity=3)   # subtotal 300
    # coupon SAVE10 reduces by 10%
    discounted = 300 * 0.9
    shipping = shipping_fee(discounted)
    expected_total = round(discounted + shipping, 2)
    assert c.total(member=False, coupon="SAVE10") == expected_total


def test_total_invalid_coupon_raises():
    c = Cart()
    c.add_item("pen", 5, quantity=1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# Edge case: empty cart total is zero, no shipping
assert Cart().total() == 0.0
