import cart
import pytest

# Helper to compute expected total via specification logic

def apply_discount(price, percent):
    return round(price * (1 - percent / 100), 2)

# Tests for add_item and remove_item behavior

def test_add_item_new_and_existing():
    c = cart.Cart()
    # Add new item
    c.add_item('apple', 0.5, 3)
    assert c.items() == {'apple': 3}
    # Adding same item with same unit_price increases quantity
    c.add_item('apple', 0.5, 2)
    assert c.items() == {'apple': 5}


def test_add_item_value_error():
    c = cart.Cart()
    # negative unit price
    with pytest.raises(ValueError):
        c.add_item('banana', -1.0, 1)
    # zero quantity
    with pytest.raises(ValueError):
        c.add_item('banana', 1.0, 0)
    # mismatched unit price for existing item
    c.add_item('orange', 2.0, 1)
    with pytest.raises(ValueError):
        c.add_item('orange', 3.0, 1)


def test_remove_item():
    c = cart.Cart()
    c.add_item('pen', 1.5, 4)
    # remove part of quantity
    c.remove_item('pen', 2)
    assert c.items() == {'pen': 2}
    # removing more than remaining should remove item entirely
    c.remove_item('pen', 5)
    assert 'pen' not in c.items()


def test_remove_item_errors():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item('nonexistent')


def test_subtotal_and_total_without_discounts():
    c = cart.Cart()
    c.add_item('a', 2.0, 1)
    c.add_item('b', 3.5, 2)  # subtotal = 2 + 7 = 9
    assert c.subtotal() == pytest.approx(9.0)
    assert c.total() == pytest.approx(9.0)


def test_bulk_discount_and_member_shipping():
    c = cart.Cart()
    c.add_item('c', 10.0, 15)  # bulk quantity >= 10 => discount
    # Bulk discount percent is defined in module; use that function
    import inspect
    spec_source = inspect.getsource(cart.bulk_discount_percent)
    # Execute the source to get the function definition
    local_dict = {}
    exec(spec_source, {}, local_dict)
    bulk_percent = local_dict['bulk_discount_percent'](15)
    expected_subtotal = 10.0 * 15
    discounted_price = apply_discount(expected_subtotal, bulk_percent)
    # shipping fee for member
    import cart as mod
    shipping = mod.shipping_fee(discounted_price, member=True)
    total_expected = round(discounted_price + shipping, 2)
    assert c.total(member=True) == pytest.approx(total_expected)


def test_coupon_application():
    # Assuming coupon codes are parsed by parse_coupon and apply to total
    c = cart.Cart()
    c.add_item('d', 5.0, 4)
    subtotal = 20.0
    # Use the module's parse_coupon to get discount percent
    discount_info = cart.parse_coupon('SAVE10')
    assert isinstance(discount_info, dict) and 'percent' in discount_info
    total_expected = apply_discount(subtotal, discount_info['percent'])
    # No member shipping for simplicity
    assert c.total(coupon='SAVE10') == pytest.approx(total_expected)
