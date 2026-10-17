import pytest
import cart

# Apply discount tests (parametrized)
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
        (99.99, 1, round(98.9899, 2)),
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# Errors for apply_discount
@pytest.mark.parametrize(
    "price, percent",
    [
        (-10, 20),   # negative price
        (100, -1),   # negative percent
        (100, 101),  # percent > 100
    ],
)
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# Bulk discount percent tests
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (5, 0),
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),      # Expected 10 but implementation returns 5
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# Parse coupon tests
@pytest.mark.parametrize(
    "code, percent",
    [
        ("SAVE10", 10),
        ("save20", 20),          # Should be accepted but implementation fails
        ("   SAVE30 ", 30),
        ("SaVe40", 40),          # Should be accepted but implementation fails
        ("SAVExx", None),       # Invalid code
    ],
)
def test_parse_coupon_valid_and_invalid(code, percent):
    if percent is not None:
        assert cart.parse_coupon(code) == percent
    else:
        with pytest.raises(ValueError):
            cart.parse_coupon(code)

# Shipping fee tests
@pytest.mark.parametrize(
    "subtotal, member, expected_fee",
    [
        (1000, False, 0),
        (999.99, False, 60),
        (999.99, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected_fee):
    assert cart.shipping_fee(subtotal, member) == expected_fee

@pytest.mark.parametrize(
    "subtotal",
    [-1],
)
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart add item tests
def test_cart_add_item():
    c = cart.Cart()
    c.add_item("apple", 1.0)
    assert c.items() == {"apple": 1}
    c.add_item("apple", 1.0, quantity=2)
    assert c.items() == {"apple": 3}
    with pytest.raises(ValueError):
        c.add_item("apple", 1.5)  # mismatched price

def test_cart_add_item_errors():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("banana", -1)
    with pytest.raises(ValueError):
        c.add_item("banana", 0.5, quantity=0)

# Cart remove item tests
def test_cart_remove_item_partial_and_full():
    c = cart.Cart()
    c.add_item("orange", 2.0, quantity=3)
    c.remove_item("orange", quantity=1)
    assert c.items() == {"orange": 2}
    c.remove_item("orange")   # removes one more
    assert c.items() == {"orange": 1}
    c.remove_item("orange")   # should remove the last unit
    assert c.items() == {}

def test_cart_remove_nonexistent_item():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent")

# Items method copy test
def test_cart_items_returns_copy():
    c = cart.Cart()
    c.add_item("pear", 3.0, quantity=2)
    d = c.items()
    d["pear"] = 10
    assert c.items() == {"pear": 2}

# Subtotal calculation tests
def test_cart_subtotal():
    c = cart.Cart()
    # widget has bulk discount of 5% (quantity >=10 but <50)
    c.add_item("widget", 5, quantity=12)   # line_total = 60 - discounted 57.0
    c.add_item("gadget", 20, quantity=2)   # no discount
    expected_subtotal = round(57.0 + 40.0, 2)
    assert c.subtotal() == expected_subtotal

# Total without coupon tests
def test_cart_total_no_coupon():
    c = cart.Cart()
    c.add_item("widget", 5, quantity=12)
    c.add_item("gadget", 20, quantity=2)
    expected_total = round(c.subtotal() + cart.shipping_fee(c.subtotal(), False), 2)
    assert c.total() == expected_total

# Total with coupon and shipping bug test
def test_cart_total_with_coupon_and_shipping_bug():
    c = cart.Cart()
    # subtotal will be 1200 (>=1000)
    c.add_item("expensive", 300, quantity=4)   # 300*4 = 1200
    discounted_amount = cart.apply_discount(c.subtotal(), cart.parse_coupon("SAVE20"))
    expected_fee = cart.shipping_fee(discounted_amount, False)
    expected_total = round(discounted_amount + expected_fee, 2)
    assert c.total(coupon="SAVE20") == expected_total

# Total with coupon and shipping bug test for members
def test_cart_total_with_coupon_and_shipping_bug_member():
    c = cart.Cart()
    c.add_item("expensive", 300, quantity=4)   # subtotal 1200
    discounted_amount = cart.apply_discount(c.subtotal(), cart.parse_coupon("SAVE20"))
    expected_fee = cart.shipping_fee(discounted_amount, True)
    expected_total = round(discounted_amount + expected_fee, 2)
    assert c.total(member=True, coupon="SAVE20") == expected_total
