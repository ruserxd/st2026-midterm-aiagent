import pytest
import cart

# Helper to create a cart with known items
def make_cart(items):
    c = cart.Cart()
    for name, unit_price, qty in items:
        c.add_item(name, unit_price, qty)
    return c

@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200.0, 15, 170.0),
        (100.0, 0, 100.0),
        (50.0, 100, 0.0),
    ]
)
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize(
    "price,percent", [(-10, 20), (50, -5), (30, 110)]
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk discount percents
@pytest.mark.parametrize(
    "qty,percent",
    [
        (5, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (150, 15),
    ]
)
def test_bulk_discount_percent(qty, percent):
    assert cart.bulk_discount_percent(qty) == percent

@pytest.mark.parametrize("qty", [0, -5, 2.3])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(int(qty)) if isinstance(qty, int) else cart.bulk_discount_percent(qty)

# coupon parsing
@pytest.mark.parametrize(
    "code,result",
    [
        ("SAVE10", 10),
        ("save20", 20),
        ("  SaVe5 ", 5),
    ]
)
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", ["SAVE0", "SAVEX", "A10", "SAVE51", "", None])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping fee tests
@pytest.mark.parametrize(
    "subtotal,member,result",
    [
        (0, False, 60),
        (100, True, 30),
        (999.99, False, 60),
        (1000, False, 0),
        (1500, True, 0),
    ]
)
def test_shipping_fee(subtotal, member, result):
    assert cart.shipping_fee(subtotal, member) == result

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart operations and calculations

def test_add_and_remove_item():
    c = cart.Cart()
    c.add_item("apple", 1.0, 3)
    assert c.items() == {"apple": 3}
    # add more of same item with same price
    c.add_item("apple", 1.0, 2)
    assert c.items() == {"apple": 5}
    # adding different price raises
    with pytest.raises(ValueError):
        c.add_item("apple", 1.5, 1)
    # remove some
    c.remove_item("apple", 3)
    assert c.items() == {"apple": 2}
    # remove remaining
    c.remove_item("apple", 2)
    assert c.items() == {}
    # removing nonexistent item raises
    with pytest.raises(KeyError):
        c.remove_item("banana", 1)

# subtotal calculation with bulk discounts
@pytest.mark.parametrize(
    "items,expected_subtotal",
    [
        ([("itemA", 10.0, 9)], 90.0),            # no discount
        ([("itemB", 20.0, 10)], 190.0),          # 5% bulk => 200-10=190
        ([("itemC", 15.0, 50)], 675.0),          # 10% bulk => 750-75=675
        ([("itemD", 30.0, 100)], 2550.0),        # 15% bulk => 3000-450=2550
        ([("itemE", 5.0, 3), ("itemF", 10.0, 7)], 65.0),
    ]
)
def test_cart_subtotal(items, expected_subtotal):
    c = make_cart(items)
    assert c.subtotal() == round(expected_subtotal, 2)

# total with coupon and shipping
@pytest.mark.parametrize(
    "items,coupon,total",
    [
        ([("x", 50.0, 1)], None, 110),  # subtotal 50, no coupon, shipping 60 -> 110
        ([("y", 500.0, 2)], None, 1080),  # subtotal 1000 free shipping => 1000
        ([("z", 200.0, 3)], "SAVE10", 360),
        ([("w", 400.0, 4)], "SAVE20", 384),
    ]
)
def test_cart_total(items, coupon, total):
    c = make_cart(items)
    assert c.total(coupon=coupon) == round(total, 2)

# empty cart total should be 0
def test_empty_cart_total():
    c = cart.Cart()
    assert c.total() == 0
