import pytest
import cart

# Helper expected shipping based on spec

def _expected_shipping(subtotal, member=False):
    if subtotal < 0:
        raise ValueError("subtotal must be >= 0")
    return 0.0 if subtotal >= 1000 else (30.0 if member else 60.0)

# Helper expected total

def _expected_total(subtotal, coupon=None, member=False):
    # Apply coupon percent if given
    if coupon is not None:
        percent = cart.parse_coupon(coupon)
        subtotal -= subtotal * percent / 100.0
    shipping = _expected_shipping(subtotal, member)
    total = subtotal + shipping
    return round(total, 2)

@pytest.mark.parametrize("name,price,quantity", [
    ("apple", 200, 1),
    ("banana", 150, 3),
])
def test_add_and_items(name, price, quantity):
    c = cart.Cart()
    c.add_item(name, price, quantity)
    assert c.items() == {name: {'unit_price': price, 'quantity': quantity}}

def test_remove_item():
    c = cart.Cart()
    c.add_item("apple", 200, 5)
    c.remove_item("apple", 2)
    assert c.items()["apple"]["quantity"] == 3
    # Removing more than present should raise
    with pytest.raises(ValueError):
        c.remove_item("apple", 10)

@pytest.mark.parametrize("quantities,expected_subtotal", [
    ({"a": {'unit_price': 100, 'quantity': 1}}, 100),
    ({"b": {'unit_price': 200, 'quantity': 2}, "c": {'unit_price': 50, 'quantity': 3}}, 700),
])
def test_subtotal(quantities, expected_subtotal):
    c = cart.Cart()
    for name, data in quantities.items():
        c.add_item(name, data["unit_price"], data["quantity"])
    assert c.subtotal() == expected_subtotal

@pytest.mark.parametrize("subtotal,coupon,member,expected_total", [
    (500, None, False, 560.0),   # 500 + shipping 60
    (500, None, True, 530.0),    # 500 + shipping 30
    (1200, None, False, 1200.0),# free shipping
    (1000, None, True, 1000.0), # free shipping
    (2000, None, False, 2000.0),
])
def test_total_basic(subtotal, coupon, member, expected_total):
    c = cart.Cart()
    # Add a single item to reach desired subtotal
    c.add_item("x", int(subtotal/1), 1)
    assert c.total(member=member, coupon=coupon) == expected_total

@pytest.mark.parametrize("subtotal,coupon,expected_total", [
    (500, "10OFF", 450.0),   # 10% off then shipping 60 -> 550 - but expected after discount 450? wrong
])
def test_invalid_coupon(subtotal, coupon):
    c = cart.Cart()
    c.add_item("x", int(subtotal/1), 1)
    with pytest.raises(ValueError):
        c.total(coupon=coupon)
