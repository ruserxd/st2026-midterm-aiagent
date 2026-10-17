import pytest
import cart
from unittest import mock

def test_add_item_valid_and_duplicate():
    c = cart.Cart()
    c.add_item("apple", 1.0, 3)
    assert c.items() == {"apple": 3}
    # add more of same item with same price
    c.add_item("apple", 1.0, 2)
    assert c.items() == {"apple": 5}

def test_add_item_invalid_price_and_quantity():
    c = cart.Cart()
    # negative price
    with pytest.raises(ValueError):
        c.add_item("banana", -1.0, 2)
    # zero quantity
    with pytest.raises(ValueError):
        c.add_item("orange", 1.0, 0)
    # non-integer quantity
    with pytest.raises(ValueError):
        c.add_item("pear", 1.0, 1.5)

def test_add_item_price_mismatch():
    c = cart.Cart()
    c.add_item("milk", 2.0, 1)
    with pytest.raises(ValueError):
        c.add_item("milk", 3.0, 1)

def test_remove_nonexistent_raises_keyerror():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("bread")

def test_remove_item_decrease_and_removal_behavior():
    c = cart.Cart()
    c.add_item("pen", 1.5, 3)
    # remove less than quantity
    c.remove_item("pen", 2)
    assert c.items() == {"pen": 1}
    # remove remaining amount should delete item
    c.remove_item("pen", 1)
    assert "pen" not in c.items()

def test_subtotal_without_discount_and_rounding(monkeypatch):
    c = cart.Cart()
    # mock bulk_discount_percent to zero discount for simplicity
    monkeypatch.setattr(cart, "bulk_discount_percent", lambda qty: 0)
    c.add_item("book", 2.333, 3)  # 6.999 total before discount
    subtotal = c.subtotal()
    assert abs(subtotal - round(6.999, 2)) < 1e-9

def test_total_with_coupon_and_shipping(monkeypatch):
    c = cart.Cart()
    c.add_item("tshirt", 20.0, 2)  # subtotal 40.0
    monkeypatch.setattr(cart, "bulk_discount_percent", lambda qty: 0)
    monkeypatch.setattr(cart, "apply_discount", lambda amount, percent: amount * (1 - percent/100))
    monkeypatch.setattr(cart, "parse_coupon", lambda code: 10 if code == "SAVE10" else ValueError("invalid"))
    spy = mock.Mock(return_value=5.0)
    monkeypatch.setattr(cart, "shipping_fee", spy)
    total_amount = c.total(coupon="SAVE10")
    expected_after_discount = 40.0 * 0.9
    assert abs(total_amount - round(expected_after_discount + 5.0, 2)) < 1e-9
    spy.assert_called_once_with(expected_after_discount, False)

def test_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("hat", 15.0, 1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
