import pytest
import cart

# Tests for apply_discount
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# Validation of errors for apply_discount
@pytest.mark.parametrize("price,percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# Tests for bulk_discount_percent
@pytest.mark.parametrize("qty,percent", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(qty, percent):
    assert cart.bulk_discount_percent(qty) == percent

# Validation of errors for bulk_discount_percent
@pytest.mark.parametrize("qty", [0, -5, 3.5])
def test_bulk_discount_percent_errors(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# Tests for parse_coupon
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    ("save20 ", 20),
    ("  SAVE5", 5),
])
def test_parse_coupon(code, result):
    assert cart.parse_coupon(code) == result

# Validation of errors for parse_coupon
@pytest.mark.parametrize("code", ["SAVEX10", "SAVE0", "SAVE51", "", "10SAVE"])
def test_parse_coupon_errors(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Tests for shipping_fee
@pytest.mark.parametrize("subtotal,member,result", [
    (1000, False, 0),
    (999.99, False, 60),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, result):
    assert cart.shipping_fee(subtotal, member) == result

# Validation of errors for shipping_fee
@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart class tests
@pytest.fixture
def empty_cart():
    return cart.Cart()

def test_add_item_increases_quantity(empty_cart):
    c = empty_cart
    c.add_item("apple", 1.0, 2)
    assert c.items() == {"apple": 2}
    c.add_item("apple", 1.0, 3)
    assert c.items() == {"apple": 5}

def test_add_item_mismatched_price(empty_cart):
    c = empty_cart
    c.add_item("banana", 0.5, 1)
    with pytest.raises(ValueError):
        c.add_item("banana", 0.6, 2)

# Test removing items
def test_remove_item_reduces_quantity_and_removes(empty_cart):
    c = empty_cart
    c.add_item("orange", 0.8, 4)
    c.remove_item("orange", 2)
    assert c.items() == {"orange": 2}
    c.remove_item("orange", 2)
    # After removal to zero, item should be removed entirely
    assert c.items() == {}

# Removing non-existent item raises KeyError
def test_remove_nonexistent_raises(empty_cart):
    c = empty_cart
    with pytest.raises(KeyError):
        c.remove_item("pear", 1)

# Subtotal calculation
def test_subtotal_calculation(empty_cart):
    c = empty_cart
    c.add_item("shirt", 20.0, 2)  # $40
    c.add_item("jeans", 50.0, 1)   # $50
    assert c.subtotal() == 90.0

# Total calculation with member and coupon
def test_total_with_member_and_coupon(empty_cart):
    c = empty_cart
    c.add_item("book", 30.0, 3)     # $90
    total = c.total(member=True, coupon="SAVE10")  # apply 10% discount then shipping
    # subtotal 90 - bulk discount percent for quantity 3 is 0
    # coupon 10% -> 81.0; shipping fee 30 (member) => 111.0
    assert total == 111.0

# Total without member, no coupon
def test_total_without_member_and_coupon(empty_cart):
    c = empty_cart
    c.add_item("pen", 5.0, 1)
    # subtotal 5 - shipping fee 60 (non-member) => 65
    assert c.total() == 65.0
