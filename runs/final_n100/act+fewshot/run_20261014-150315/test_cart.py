import pytest
import cart

# ---------- apply_discount -------------------------------------------------

def test_apply_discount_valid():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0
    # rounding to two decimals
    assert cart.apply_discount(33.333, 10) == round(33.333 * 0.9, 2)

def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        cart.apply_discount(-1, 10)


def test_apply_discount_invalid_percent():
    for bad in (-5, 105):
        with pytest.raises(ValueError):
            cart.apply_discount(100, bad)

# ---------- bulk_discount_percent ------------------------------------------

def test_bulk_discount_percent_bounds():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

def test_bulk_discount_percent_invalid():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-10)

# ---------- parse_coupon ----------------------------------------------------

def test_parse_coupon_valid_cases():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save5 ") == 5
    assert cart.parse_coupon(" SAVE50") == 50
    # case-insensitive
    assert cart.parse_coupon("SaVe25") == 25


def test_parse_coupon_invalid():
    for bad in ["SAVE0", "SAVE51", "INVALID", "SAVExx", ""]:
        with pytest.raises(ValueError):
            cart.parse_coupon(bad)

# ---------- shipping_fee -----------------------------------------------------

def test_shipping_fee_free_and_standard():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(999.99) == 60
    # member discount
    assert cart.shipping_fee(200, member=True) == 30


def test_shipping_fee_invalid_subtotal():
    with pytest.raises(ValueError):
        cart.shipping_fee(-1)

# ---------- Cart class tests ----------------------------------------------

@pytest.fixture
def empty_cart():
    return cart.Cart()


def test_cart_initially_empty(empty_cart):
    assert empty_cart.items() == {}
    assert empty_cart.subtotal() == 0.0
    assert empty_cart.total() == 0.0


def test_add_and_remove_items(empty_cart):
    c = empty_cart
    c.add_item("apple", 1.00, quantity=3)
    assert c.items()["apple"] == (1.00, 3)
    # adding more increases quantity
    c.add_item("apple", 1.00, quantity=2)
    assert c.items()["apple"] == (1.00, 5)
    c.remove_item("apple", quantity=4)
    assert c.items()["apple"] == (1.00, 1)
    # remove remaining
    c.remove_item("apple")
    assert "apple" not in c.items()


def test_subtotal_and_total_no_coupon(empty_cart):
    c = empty_cart
    c.add_item("banana", 0.50, quantity=10)  # subtotal 5
    assert c.subtotal() == 5.0
    # no coupon, non-member: shipping fee 60 applied -> total 65
    assert c.total() == round(5.0 + 60, 2)
    # member discount on shipping
    assert c.total(member=True) == round(5.0 + 30, 2)


def test_total_with_coupon_and_bulk_discount(empty_cart):
    c = empty_cart
    # add 50 units of widget at $10 each -> bulk discount percent 10%
    c.add_item("widget", 10.00, quantity=50)
    # subtotal before discounts
    assert c.subtotal() == 500.0
    # compute expected: apply bulk discount 10% on the item price? Actually bulk_discount_percent is per-item; but Cart.total uses coupon only.
    # So we only test coupon logic here.
    total_without_coupon = round(500.0 + 60, 2)
    assert c.total() == total_without_coupon
    # apply a valid coupon of 20%
    expected_after_coupon = cart.apply_discount(total_without_coupon, 20)
    assert c.total(coupon="SAVE20") == round(expected_after_coupon, 2)


def test_total_with_invalid_coupon(empty_cart):
    c = empty_cart
    c.add_item("thing", 100.0)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# ---------- Edge cases ------------------------------------------------------

def test_remove_nonexistent_item(empty_cart):
    c = empty_cart
    # Removing item not in cart should do nothing and keep cart unchanged
    c.remove_item("ghost")
    assert c.items() == {}
