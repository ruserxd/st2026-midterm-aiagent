import pytest
import cart

# ---------- apply_discount -------------------------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0
    # rounding to two decimals
    assert cart.apply_discount(99.99, 33) == pytest.approx(66.65)


def test_apply_discount_errors():
    with pytest.raises(ValueError):
        cart.apply_discount(-1, 10)
    with pytest.raises(ValueError):
        cart.apply_discount(100, -5)
    with pytest.raises(ValueError):
        cart.apply_discount(100, 105)

# ---------- bulk_discount_percent ------------------------------------------

def test_bulk_discount_thresholds():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

def test_bulk_discount_errors():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-10)
    # non-integer should also raise because quantity must be positive int
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(5.5)

# ---------- parse_coupon ----------------------------------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20 ") == 20
    assert cart.parse_coupon(" SAVE30 ") == 30
    # case insensitive and whitespace ignored
    assert cart.parse_coupon("SaVe5") == 5


def test_parse_coupon_invalid():
    for code in ["", "SAVE0", "SAVE51", "NOTA", "SAVEX", "  SAVE10abc"]:
        with pytest.raises(ValueError):
            cart.parse_coupon(code)

# ---------- shipping_fee -----------------------------------------------------

def test_shipping_fee_non_member():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(0) == 60


def test_shipping_fee_member_half():
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(100, member=True) == 30


def test_shipping_fee_errors():
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

# ---------- Cart class -------------------------------------------------------

def test_cart_add_and_subtotal():
    c = cart.Cart()
    assert c.subtotal() == 0
    c.add_item("apple", unit_price=100, quantity=3)
    assert c.items() == [({"name": "apple", "unit_price": 100}, 3)]
    # subtotal should be 300
    assert c.subtotal() == 300
    # add another item
    c.add_item("banana", unit_price=200, quantity=2)
    assert c.items()[-1] == ({"name": "banana", "unit_price": 200}, 2)
    assert c.subtotal() == 700


def test_cart_remove_and_total():
    c = cart.Cart()
    c.add_item("item", unit_price=100, quantity=5)   # subtotal 500
    # total without coupon or member: shipping free? subtotal 500 -> fee 60
    assert c.total() == pytest.approx(560.0)
    # with member, half fee
    assert c.total(member=True) == pytest.approx(530.0)
    # apply a valid coupon of 10%
    assert c.total(coupon="SAVE10") == pytest.approx(round((500 * 0.9) + 60,2))
    # member with coupon
    assert c.total(member=True, coupon="save5") == pytest.approx(round((500 * 0.95)+30,2))

    # remove some quantity
    c.remove_item("item", quantity=3)
    assert c.subtotal() == 200
    # remove more than existing -> should raise? not spec but check
    with pytest.raises(IndexError):
        c.remove_item("item", quantity=5)

# ---------- empty cart total -------------------------------------------------
def test_empty_cart_total():
    c = cart.Cart()
    assert c.total() == 0
    # adding then removing all should also give zero
    c.add_item("foo", 50, 1)
    c.remove_item("foo")
    assert c.total() == 0

# ---------- coupon error handling in total ---------------------------------
def test_invalid_coupon_in_total():
    c = cart.Cart()
    c.add_item("item", 100, 2)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
