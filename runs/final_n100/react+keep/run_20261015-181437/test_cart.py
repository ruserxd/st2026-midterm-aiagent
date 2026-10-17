import pytest
import cart

# ---------- Helper functions for expected calculations ----------

def expected_bulk_discount(quantity):
    if quantity >= 100:
        return 15
    elif quantity >= 50:
        return 10
    elif quantity >= 10:
        return 5
    else:
        return 0

def apply_expected(price, percent):
    if price < 0 or not (0 <= percent <= 100):
        raise ValueError("invalid inputs")
    return round(price * (1 - percent / 100), 2)

# ---------- Coupon parsing tests ----------

def test_parse_coupon_valid_cases():
    # Case-insensitive and stripped whitespace
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon("  Save30  ") == 30


def test_parse_coupon_invalid_cases():
    with pytest.raises(ValueError):
        cart.parse_coupon("SAV10")   # missing 'E'
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE0")   # percent < 1
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE51")  # percent > 50
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE-5")  # negative
    with pytest.raises(ValueError):
        cart.parse_coupon("ABCD10")   # wrong prefix

# ---------- Shipping fee tests ----------

def test_shipping_fee_regular_and_member():
    assert cart.shipping_fee(500, member=False) == 60
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(0, member=False) == 60


def test_shipping_fee_free_for_large_subtotal():
    assert cart.shipping_fee(1000, member=False) == 0
    assert cart.shipping_fee(1500, member=True) == 0


def test_shipping_fee_invalid_inputs():
    with pytest.raises(ValueError):
        cart.shipping_fee(-1)

# ---------- Apply discount tests ----------

def test_apply_discount_basic_cases():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(123.45, 10) == round(123.45 * 0.9, 2)


def test_apply_discount_invalid_inputs():
    with pytest.raises(ValueError):
        cart.apply_discount(-5, 10)
    with pytest.raises(ValueError):
        cart.apply_discount(50, -1)
    with pytest.raises(ValueError):
        cart.apply_discount(50, 101)

# ---------- Cart class tests ----------

@pytest.fixture
def empty_cart():
    return cart.Cart()


def test_add_item_new_and_existing(empty_cart):
    # Add new item
    empty_cart.add_item("apple", unit_price=1.0, quantity=5)
    assert empty_cart.items() == {"apple": 5}
    # Adding the same item increases quantity
    empty_cart.add_item("apple", unit_price=1.0, quantity=3)
    assert empty_cart.items() == {"apple": 8}


def test_add_item_invalid_inputs(empty_cart):
    with pytest.raises(ValueError):
        empty_cart.add_item("banana", unit_price=-1, quantity=2)
    with pytest.raises(ValueError):
        empty_cart.add_item("banana", unit_price=1, quantity=0)
    # Changing price of existing item should raise ValueError
    empty_cart.add_item("pear", unit_price=2.0, quantity=3)
    with pytest.raises(ValueError):
        empty_cart.add_item("pear", unit_price=3.0, quantity=1)


def test_remove_item(empty_cart):
    empty_cart.add_item("orange", unit_price=0.5, quantity=10)
    # Remove part of the quantity
    empty_cart.remove_item("orange", quantity=4)
    assert empty_cart.items() == {"orange": 6}
    # Removing remaining quantity removes item completely
    empty_cart.remove_item("orange", quantity=6)
    assert empty_cart.items() == {}


def test_remove_nonexistent_item(empty_cart):
    with pytest.raises(KeyError):
        empty_cart.remove_item("nonexistent")


def test_subtotal_bulk_discount_logic():
    c = cart.Cart()
    # 12 apples: unit price 1.0, bulk discount 5%
    c.add_item("apple", 1.0, quantity=12)
    expected_price = 12 * 1.0
    expected_price -= expected_bulk_discount(12) / 100 * expected_price
    assert round(c.subtotal(), 2) == round(expected_price, 2)
    # 55 bananas: unit price 2.0, bulk discount 10%
    c.add_item("banana", 2.0, quantity=55)
    banana_total = 55 * 2.0
    banana_discounted = banana_total - expected_bulk_discount(55) / 100 * banana_total
    assert round(c.subtotal(), 2) == round(expected_price + banana_discounted, 2)


def test_cart_total_with_coupon_and_shipping(empty_cart):
    # Setup items: 10 oranges at $5 each => bulk discount 5%
    empty_cart.add_item("orange", unit_price=5.0, quantity=10)
    # Subtotal calculation
    subtotal_before = empty_cart.subtotal()
    # Apply coupon SAVE20
    amount_after_coupon = apply_expected(subtotal_before, 20)
    shipping = cart.shipping_fee(amount_after_coupon, member=False)
    total_expected = round(amount_after_coupon + shipping, 2)
    assert empty_cart.total(coupon="SAVE20") == total_expected


def test_cart_total_no_shipping_on_empty():
    c = cart.Cart()
    assert c.total() == 0.0

# ---------- Edge case: negative and zero values for quantity ----------

def test_negative_quantity_remove(empty_cart):
    empty_cart.add_item("kiwi", unit_price=1.5, quantity=3)
    with pytest.raises(KeyError):
        empty_cart.remove_item("kiwi", quantity=-1)  # negative should raise KeyError as item not found
