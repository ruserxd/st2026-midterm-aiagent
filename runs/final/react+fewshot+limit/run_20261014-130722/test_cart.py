import pytest
import cart

# Helper for invalid values
@pytest.mark.parametrize("price, percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# valid discount calculation
@pytest.mark.parametrize("price, percent, expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 50, 25.0),
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# bulk_discount_percent edge cases
@pytest.mark.parametrize("qty, expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

# bulk_discount_percent invalid
@pytest.mark.parametrize("qty", [0, -5, 3.2, "10"])
def test_bulk_discount_percent_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# parse_coupon valid and invalid
@pytest.mark.parametrize("code, expected", [
    ("SAVE10", 10),
    ("save5", 5),
    (" SAVE20 ", 20),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVEX", "INVALID", "SAVE51", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal, member, expected", [
    (0, False, 60),
    (999.99, True, 30),
    (1000, False, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# Cart behavior tests
def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item("apple", 1.0)
    c.add_item("banana", 2.5, 3)
    assert c.items() == {"apple":1, "banana":3}
    # Adding same item with same price increases quantity
    c.add_item("apple", 1.0, 4)
    assert c.items()["apple"] == 5

# adding with mismatched unit price raises
def test_cart_add_mismatch_price():
    c = cart.Cart()
    c.add_item("pear", 3.0)
    with pytest.raises(ValueError):
        c.add_item("pear", 2.9)

# removing items and zero quantity removal
def test_cart_remove_and_zero_quantity():
    c = cart.Cart()
    c.add_item("orange", 1.5, 5)
    c.remove_item("orange", 3)
    assert c.items()["orange"] == 2
    # remove more than remaining to trigger removal
    c.remove_item("orange", 3)
    assert "orange" not in c.items()

# removing non-existent item raises KeyError
def test_cart_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("pineapple")

# subtotal calculation with bulk discount
def test_cart_subtotal_bulk_discount():
    c = cart.Cart()
    # 10 units of $1 => bulk discount 5%
    c.add_item("item", 1.0, 10)
    assert c.subtotal() == round(1.0*10 * (1-0.05), 2)

# total with coupon and shipping
def test_cart_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("widget", 100.0, 5)  # no bulk discount
    subtotal = c.subtotal()  # 500
    # apply coupon SAVE10 -> 450
    total = c.total(coupon="SAVE10")
    # shipping on 450 (member False) -> 60
    assert total == round(450 + 60, 2)

# total with member discount on shipping only
def test_cart_total_member_shipping():
    c = cart.Cart()
    c.add_item("gadget", 200.0, 1)
    subtotal = c.subtotal()  # 200
    total = c.total(member=True)
    assert total == round(200 + 30, 2)

# empty cart costs zero and no shipping
def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0.00
