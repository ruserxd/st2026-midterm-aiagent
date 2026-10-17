import pytest
import cart

# Helper to create a cart with known items

def make_cart():
    c = cart.Cart()
    # add some items for testing bulk discounts and totals
    c.add_item("apple", 10.0, 5)   # no bulk discount
    c.add_item("banana", 20.0, 12) # bulk discount 5%
    return c

# ----------------- apply_discount -----------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize(
    "price, percent, expected",
    [
        (100, 0, 100.0),
        (100, 50, 50.0),
        (99.999, 10, 90.00),  # rounding
    ],
)
def test_apply_discount_variants(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@ pytest.mark.parametrize(
    "price, percent",
    [(-1, 10), (100, -5), (100, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ----------------- bulk_discount_percent -----------------

def test_bulk_discount_brackets():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("quantity", [0, -5, 2.5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ----------------- parse_coupon -----------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20 ") == 20
    assert cart.parse_coupon(" SAVE30") == 30

@ pytest.mark.parametrize("code", ["SAVEX", "1234", "save0", "SAVE51", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ----------------- shipping_fee -----------------

def test_shipping_fee():
    assert cart.shipping_fee(999) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(2000) == 0
    assert cart.shipping_fee(800, member=True) == 30
    assert cart.shipping_fee(1200, member=True) == 0

@ pytest.mark.parametrize("subtotal", [-1, -5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ----------------- Cart methods -----------------

def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item("widget", 5.0, 3)
    assert c.items() == {"widget": 3}
    # adding same item increases quantity if price matches
    c.add_item("widget", 5.0, 2)
    assert c.items() == {"widget": 5}

    # mismatched unit_price raises ValueError
    with pytest.raises(ValueError):
        c.add_item("widget", 6.0, 1)

    # invalid price or quantity raise ValueError
    with pytest.raises(ValueError):
        c.add_item("gadget", -1.0, 2)
    with pytest.raises(ValueError):
        c.add_item("gadget", 3.0, 0)

def test_cart_remove_and_items():
    c = cart.Cart()
    c.add_item("itemA", 10.0, 4)
    c.remove_item("itemA", 2)
    assert c.items() == {"itemA": 2}
    # removing more than present removes the item
    c.remove_item("itemA", 3)
    assert c.items() == {}
    # removing non-existent key raises KeyError
    with pytest.raises(KeyError):
        c.remove_item("missing", 1)

# ----------------- subtotal calculations -----------------

def test_subtotal_no_discount():
    c = cart.Cart()
    c.add_item("itemX", 20.0, 4)   # no bulk discount
    assert c.subtotal() == 80.00

def test_subtotal_with_bulk_discount():
    c = cart.Cart()
    # 12 bananas with unit price 20 -> bulk discount 5%
    c.add_item("banana", 20.0, 12)
    expected = round(20.0 * 12 * (1 - 0.05), 2)  # 240 * 0.95
    assert c.subtotal() == expected

def test_subtotal_empty_cart():
    c = cart.Cart()
    assert c.subtotal() == 0.00

# ----------------- total calculations -----------------

def test_total_without_coupon_or_shipping_fee_free():
    c = make_cart()
    # subtotal calculation: apple(10*5=50) + banana(20*12=240) with bulk discounts
    expected_subtotal = round(10.0 * 5 + 20.0 * 12 * (1 - cart.bulk_discount_percent(12)/100), 2)
    assert c.subtotal() == expected_subtotal
    total = c.total()
    # no coupon, not member: shipping fee should be applied if subtotal < 1000
    expected_shipping = 60 if expected_subtotal < 1000 else 0
    assert total == round(expected_subtotal + expected_shipping, 2)

def test_total_with_coupon_and_member():
    c = make_cart()
    # apply coupon SAVE20 (20% off after subtotal)
    subtotal_after_coupon = cart.apply_discount(c.subtotal(), cart.parse_coupon("SAVE20"))
    shipping = cart.shipping_fee(subtotal_after_coupon, member=True)
    expected_total = round(subtotal_after_coupon + shipping, 2)
    assert c.total(member=True, coupon="SAVE20") == expected_total

# ----------------- total on empty cart -----------------

def test_total_empty_cart_zero():
    c = cart.Cart()
    assert c.total() == 0.00
