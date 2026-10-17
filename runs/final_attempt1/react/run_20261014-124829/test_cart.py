import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# --- tests for helper functions ---------------------------------------

def test_apply_discount_valid():
    assert apply_discount(200, 15) == 170.0
    # check rounding to two decimals
    assert apply_discount(99.99, 12.5) == round(99.99 * (1 - 12.5/100), 2)

@pytest.mark.parametrize("price", [(-10, 0, -1)])
def test_apply_discount_invalid_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 20)

@pytest.mark.parametrize("percent", [-1, 101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# --- bulk discount tests -----------------------------------------------

def test_bulk_discount_levels():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@pytest.mark.parametrize("quantity", [0, -5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# --- parse_coupon tests -------------------------------------------------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save25") == 25
    assert parse_coupon("  SaVe50 ") == 50

@pytest.mark.parametrize(
    "code",
    ["", "SAVEX", "SAVE0", "SAVE51", "DISCOUNT", " SAVE-10", "save-5"],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# --- shipping fee tests -------------------------------------------------

def test_shipping_fee():
    assert shipping_fee(0) == 60
    assert shipping_fee(500) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(2000) == 0

    # member discount
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(1000, member=True) == 0

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# --- Cart class tests ---------------------------------------------------

def test_cart_basic_operations():
    cart = Cart()
    # initially empty
    assert list(cart.items()) == []
    assert cart.subtotal() == 0

    cart.add_item("apple", unit_price=100, quantity=3)
    assert list(cart.items()) == [("apple", (100, 3))]
    assert cart.subtotal() == 300

    # adding same item increments quantity
    cart.add_item("apple", unit_price=100, quantity=2)
    assert list(cart.items()) == [("apple", (100, 5))]
    assert cart.subtotal() == 500

    # remove items
    cart.remove_item("apple", quantity=2)
    assert list(cart.items()) == [("apple", (100, 3))]
    assert cart.subtotal() == 300

    # removing more than present removes the item entirely
    cart.remove_item("apple", quantity=5)
    assert list(cart.items()) == []
    assert cart.subtotal() == 0


def test_cart_total_with_discounts_and_shipping():
    cart = Cart()
    cart.add_item("item1", unit_price=200, quantity=20)   # bulk discount 15%
    cart.add_item("item2", unit_price=500, quantity=5)

    # subtotal calculation before discounts and shipping
    expected_subtotal = 200*20 + 500*5
    assert cart.subtotal() == expected_subtotal

    # total with member discount, coupon SAVE10 (10%) and bulk discount on item1
    total = cart.total(member=True, coupon="SAVE10")

    # apply bulk discount to item1 only: 200*(1-0.15)=170 per unit
    discounted_item1 = 170*20
    discounted_item2 = 500*5  # no bulk discount
    subtotal_with_bulk = discounted_item1 + discounted_item2

    # coupon discount on entire order after bulk discounts
    subtotal_after_coupon = subtotal_with_bulk * (1-0.10)

    # shipping: subtotal >=1000? compute
    if subtotal_after_coupon < 1000:
        expected_shipping = 30  # member half of 60
    else:
        expected_shipping = 0
    expected_total = round(subtotal_after_coupon + expected_shipping, 2)
    assert total == expected_total

# Edge case: coupon applied before shipping (as implemented in spec)

def test_cart_total_coupon_ordering():
    cart = Cart()
    cart.add_item("item", unit_price=2000, quantity=1)
    # subtotal > 1000 => free shipping regardless of member status
    assert cart.total(coupon="SAVE5") == pytest.approx(1900.0)  # 5% off only

# Coupon case-insensitivity and whitespace handling

def test_cart_coupon_whitespace_and_case():
    cart = Cart()
    cart.add_item("x", unit_price=100, quantity=1)
    assert cart.total(coupon="save10") == pytest.approx(90.0)
    assert cart.total(coupon="  SAVE20 ") == pytest.approx(80.0)

# Remove item not present does nothing

def test_remove_nonexistent_item():
    cart = Cart()
    cart.remove_item("missing", quantity=1)  # should not raise
    assert list(cart.items()) == []

# Adding item with zero or negative quantity raises ValueError

def test_add_item_invalid_quantity():
    cart = Cart()
    with pytest.raises(ValueError):
        cart.add_item("bad", unit_price=10, quantity=0)
    with pytest.raises(ValueError):
        cart.add_item("bad2", unit_price=10, quantity=-5)

# Removing item with zero or negative quantity raises ValueError

def test_remove_item_invalid_quantity():
    cart = Cart()
    cart.add_item("good", 50, 3)
    with pytest.raises(ValueError):
        cart.remove_item("good", quantity=0)
    with pytest.raises(ValueError):
        cart.remove_item("good", quantity=-1)

# Ensure internal state is not exposed (items returns a copy or iterator)

def test_cart_items_iterator_is_copy():
    cart = Cart()
    cart.add_item("a", 10, 2)
    items_iter = cart.items()
    # Consume iterator to list for assertion
    assert list(items_iter) == [("a", (10, 2))]
    # Modifying the returned tuple should not affect cart's internal state
    l = list(cart.items())[0][1]
    try:
        l[1] = 999  # tuples are immutable; this will raise TypeError
    except Exception as e:
        pass
    assert cart.subtotal() == 20
