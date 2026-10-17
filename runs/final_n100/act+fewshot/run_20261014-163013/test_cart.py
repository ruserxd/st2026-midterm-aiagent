import pytest
import cart

# Test apply_discount
@pytest.mark.parametrize("price, percent, expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# Invalid price
@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

# Invalid percent
@pytest.mark.parametrize("percent", [-5, 101, 200])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# Test bulk_discount_percent
@pytest.mark.parametrize("quantity, expected", [
    (0, ValueError),
    (5, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    if quantity == 0:
        with pytest.raises(ValueError):
            cart.bulk_discount_percent(quantity)
    else:
        assert cart.bulk_discount_percent(quantity) == expected

# Test parse_coupon
@pytest.mark.parametrize("code, expected", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVE0",
    "SAVE51",
    "DISCOUNT10",
    "save-5",
    " ",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# Test shipping_fee
@pytest.mark.parametrize("subtotal, member, expected", [
    (1000, False, 0),
    (999.99, False, 60),
    (500, True, 30),
    (0, False, 60),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# Shipping fee invalid subtotal
@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart functionality
def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item("apple", 1.0, 3)
    c.add_item("banana", 2.5)
    assert c.items() == {"apple": 3, "banana": 1}

# Adding same item with different price raises ValueError

def test_cart_add_price_mismatch():
    c = cart.Cart()
    c.add_item("apple", 1.0)
    with pytest.raises(ValueError):
        c.add_item("apple", 2.0)

# Removing items

def test_cart_remove_items():
    c = cart.Cart()
    c.add_item("apple", 1.0, 5)
    c.remove_item("apple", 3)
    assert c.items() == {"apple": 2}
    # remove more than existing should remove item
    c.remove_item("apple", 5)
    assert c.items() == {}

# Removing non-existent raises KeyError

def test_cart_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("pear")

# Subtotal calculation with bulk discounts

def test_cart_subtotal_bulk_discount():
    c = cart.Cart()
    # 10 apples, unit price 1 => bulk discount 5%
    c.add_item("apple", 1.0, 10)
    # 55 bananas, unit price 2 => bulk discount 10%
    c.add_item("banana", 2.0, 55)
    subtotal = cart.apply_discount(10*1.0, 5) + cart.apply_discount(55*2.0, 10)
    assert c.subtotal() == round(subtotal, 2)

# Total with coupon and shipping

def test_cart_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("item", 100.0, 5)  # no bulk discount
    # subtotal = 500
    total_before_coupon = 500
    total_after_coupon = cart.apply_discount(total_before_coupon, 10)
    shipping = cart.shipping_fee(total_after_coupon, member=False)
    expected_total = round(total_after_coupon + shipping, 2)
    assert c.total(coupon="SAVE10") == expected_total

# Total with member discount and no coupon

def test_cart_total_member_no_coupon():
    c = cart.Cart()
    c.add_item("item", 200.0, 1)
    # subtotal = 200
    shipping = cart.shipping_fee(200, member=True)  # 30
    expected = round(200 + shipping, 2)
    assert c.total(member=True) == expected

# Total for empty cart is zero

def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0
