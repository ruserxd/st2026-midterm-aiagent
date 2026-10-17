import pytest
import cart

# --- Basic helper calculations based on spec ---

# ------------------- apply_discount -------------------

def test_apply_discount_valid():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(50, 20) == 40.0
    # percent at bounds
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(100, 100) == 0.0

def test_apply_discount_invalid():
    with pytest.raises(ValueError):
        cart.apply_discount(-10, 5)
    with pytest.raises(ValueError):
        cart.apply_discount(10, -1)
    with pytest.raises(ValueError):
        cart.apply_discount(10, 101)

# ------------------- bulk_discount_percent -------------------
@pytest.mark.parametrize("qty,expected", [
    (5,0), (9,0), (10,5), (49,5), (50,10), (99,10), (100,15), (150,15)
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

def test_bulk_discount_percent_invalid():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-5)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(3.5)

# ------------------- parse_coupon -------------------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10",10), ("save20",20), ("  SaVe30  ",30)
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

def test_parse_coupon_invalid():
    with pytest.raises(ValueError):
        cart.parse_coupon("INVALID")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE0")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE51")
    with pytest.raises(ValueError):
        cart.parse_coupon("  ")

# ------------------- shipping_fee -------------------
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60), (999.99, False, 60), (1000, False, 0), (1500, True, 0), (500, True, 30)
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

def test_shipping_fee_invalid():
    with pytest.raises(ValueError):
        cart.shipping_fee(-1)

# ------------------- Cart tests -------------------
@pytest.fixture
def empty_cart():
    return cart.Cart()

# 1. Initialization

def test_empty_cart_initialization(empty_cart):
    assert empty_cart.items() == {}
    assert empty_cart.subtotal() == 0.0
    assert empty_cart.total() == 0.0

# 2. Adding items

def test_add_item_and_items(empty_cart):
    empty_cart.add_item("apple", 1.00, 3)
    assert empty_cart.items() == {"apple":3}
    # adding same item increases quantity
    empty_cart.add_item("apple", 1.00, 2)
    assert empty_cart.items()["apple"] == 5
    # adding new item
    empty_cart.add_item("banana", 0.50)
    assert empty_cart.items() == {"apple":5, "banana":1}

# 3. Validation of quantity and price

def test_add_item_invalid(empty_cart):
    with pytest.raises(ValueError):
        empty_cart.add_item("orange", -1.00, 2)
    with pytest.raises(ValueError):
        empty_cart.add_item("orange", 1.00, 0)
    with pytest.raises(ValueError):
        empty_cart.add_item("orange", 1.00, 3.5)

# 4. Unit price consistency

def test_add_same_name_different_price(empty_cart):
    empty_cart.add_item("pear", 2.00, 1)
    with pytest.raises(ValueError):
        empty_cart.add_item("pear", 3.00, 1)

# 5. Removing items

def test_remove_item(empty_cart):
    empty_cart.add_item("item", 10.0, 5)
    empty_cart.remove_item("item", 2)
    assert empty_cart.items()["item"] == 3
    # removing more than present removes it completely
    empty_cart.remove_item("item", 4)
    assert "item" not in empty_cart.items()


def test_remove_nonexistent_item(empty_cart):
    with pytest.raises(KeyError):
        empty_cart.remove_item("nonexistent", 1)

# 6. Subtotal calculations with bulk discounts

def test_subtotal_with_bulk(empty_cart):
    # 9 units - no discount
    empty_cart.add_item("small", 10.0, 9)
    assert empty_cart.subtotal() == 90.0
    # 10 units - 5% discount on that item
    c = cart.Cart()
    c.add_item("medium", 20.0, 10)
    assert c.subtotal() == round(20*10*0.95,2)  # 190.0
    # multiple items with different discounts
    c.add_item("large", 5.0, 50)  # 10% discount on large
    expected = round(20*10*0.95 + 5*50*0.90,2)
    assert c.subtotal() == expected

# 7. Total calculation with coupon and shipping

def test_total_with_coupon_and_shipping(empty_cart):
    empty_cart.add_item("item", 100.0, 1)  # subtotal 100
    total = empty_cart.total(coupon="SAVE10")
    # 10% off: 90 + shipping 60 (non-member) = 150
    assert total == round(90+60,2)
    # member with coupon
    total_member = empty_cart.total(member=True, coupon="SAVE20")
    # 20% off: 80 + shipping 30 = 110
    assert total_member == round(80+30,2)

# 8. Total for empty cart (no shipping)

def test_total_empty():
    c = cart.Cart()
    assert c.total() == 0.0
    assert c.total(member=True) == 0.0
    assert c.total(coupon="SAVE10") == 0.0
