# test_cart.py
import pytest
import cart

# Helper function tests

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

def test_apply_discount_rounding():
    # 1% of 99.99 is 0.9999 → rounded to 2 decimals: 0.99
    assert cart.apply_discount(99.99, 1) == round(99.99 * 0.99, 2)

def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        cart.apply_discount(-10, 5)

def test_apply_discount_invalid_percent():
    for pct in (-1, 101):
        with pytest.raises(ValueError):
            cart.apply_discount(100, pct)


def test_bulk_discount_percent_basic():
    assert cart.bulk_discount_percent(1) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(20) == 10


def test_parse_coupon_success():
    # coupon format: "CODE:DISCOUNT%" e.g. "SAVE20:20%"
    assert cart.parse_coupon("SAVE20:20%") == ("SAVE20", 20)


def test_parse_coupon_invalid_format():
    with pytest.raises(ValueError):
        cart.parse_coupon("INVALID")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE:XYZ%")


def test_shipping_fee_non_member():
    # subtotal below threshold → flat rate
    assert cart.shipping_fee(40, member=False) == 5.0
    # above threshold → free
    assert cart.shipping_fee(70, member=False) == 0.0


def test_shipping_fee_member():
    # Member has no fee regardless of amount
    for subtotal in (10, 200):
        assert cart.shipping_fee(subtotal, member=True) == 0.0

# Cart class tests

@pytest.fixture
def empty_cart():
    return cart.Cart()


def test_add_and_items(empty_cart):
    empty_cart.add_item("Apple", 1.00)
    assert empty_cart.items() == [({"name": "Apple",
                                   "unit_price": 1.0,
                                   "quantity": 1},
                                  1.0)]


def test_remove_item_partial_quantity(empty_cart):
    empty_cart.add_item("Banana", 0.5, quantity=3)
    empty_cart.remove_item("Banana")
    assert empty_cart.items() == [({"name": "Banana",
                                   "unit_price": 0.5,
                                   "quantity": 2},
                                  1.0)]


def test_remove_item_completely(empty_cart):
    empty_cart.add_item("Carrot", 0.25, quantity=2)
    empty_cart.remove_item("Carrot", quantity=2)
    assert empty_cart.items() == []


def test_subtotal_and_total_basic(empty_cart):
    empty_cart.add_item("Milk", 3.0, quantity=2)   # 6.0
    empty_cart.add_item("Eggs", 0.2, quantity=12)  # 2.4
    assert empty_cart.subtotal() == 8.4
    # No discount or coupon, non‑member shipping
    assert empty_cart.total(member=False, coupon=None) == 13.4  # 8.4 + 5


def test_total_with_bulk_discount(empty_cart):
    empty_cart.add_item("Widget", 10.0, quantity=15)  # subtotal 150
    # Bulk discount: 5% for 10‑19 items → 7.5
    assert cart.bulk_discount_percent(15) == 5
    total = empty_cart.total()
    # subtotal 150 - 7.5 bulk + 0 shipping (subtotal > threshold)
    assert total == 142.5


def test_total_with_coupon_and_member(empty_cart):
    empty_cart.add_item("Book", 20.0, quantity=2)  # 40
    coupon_code = "SAVE10:10%"
    empty_cart.total(member=True, coupon=coupon_code)
    # subtotal 40 → bulk discount 0; member shipping 0; coupon 10% off => 36
    assert empty_cart.total(member=True, coupon=coupon_code) == 36.0


def test_total_invalid_coupon(empty_cart):
    empty_cart.add_item("Pen", 1.5)
    with pytest.raises(ValueError):
        empty_cart.total(coupon="BADCODE")
