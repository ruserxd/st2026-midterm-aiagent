import pytest
import cart

# ---------- Unit function tests ----------

# apply_discount

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize("price, percent", [(-10, 20), (100, -5), (50, 105)])
def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent

def test_bulk_discount_percent_levels():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

def test_bulk_discount_percent_invalid():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-1)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0.5)

# parse_coupon

def test_parse_coupon_valid_cases():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon(" save20 ") == 20
    assert cart.parse_coupon("SaVe1") == 1

@ pytest.mark.parametrize("code", ["INVALID", "SAVExx", "", "SAVE0", "SAVE51", "SAVEX5", "1234"]) 
def test_parse_coupon_invalid_cases(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee

def test_shipping_fee_free_for_eligible():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1200.50) == 0

@ pytest.mark.parametrize("subtotal, expected", [ (999.99, 60), (500, 30), (200, 30)])
def test_shipping_fee_for_non_members(subtotal, expected):
    assert cart.shipping_fee(subtotal) == expected

# Member pays half fee (rounded to integer if needed)
@ pytest.mark.parametrize("subtotal, expected", [ (999.99, 30), (500, 30), (200, 30)])
def test_shipping_fee_for_members(subtotal, expected):
    assert cart.shipping_fee(subtotal, member=True) == expected

# Shipping fee invalid subtotal
@ pytest.mark.parametrize("subtotal", [-10, -5.5])
def test_shipping_fee_invalid_subtotal(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class tests ----------

@pytest.fixture
def empty_cart():
    return cart.Cart()

# Adding items should store unit price and quantity correctly

def test_add_item_basic(empty_cart):
    empty_cart.add_item("apple", 100, 3)
    assert "apple" in empty_cart.items()
    assert empty_cart.items()["apple"] == (100, 3)

# Adding same item increases quantity and keeps unit price

def test_add_same_item_increases_quantity(empty_cart):
    empty_cart.add_item("banana", 50, 2)
    empty_cart.add_item("banana", 50, 4)
    assert empty_cart.items()["banana"] == (50, 6)

# Removing items reduces quantity and removes key when zero

def test_remove_item_reduces_quantity(empty_cart):
    empty_cart.add_item("cherry", 75, 5)
    empty_cart.remove_item("cherry", 2)
    assert empty_cart.items()["cherry"] == (75, 3)

@ pytest.mark.parametrize("remove_qty", [5, 10])
def test_remove_item_removes_key_when_zero(empty_cart, remove_qty):
    empty_cart.add_item("date", 120, 5)
    empty_cart.remove_item("date", remove_qty)
    assert "date" not in empty_cart.items()

# Removing more than exists should set quantity to zero (remove key) but no negative quantity

def test_remove_more_than_exists(empty_cart):
    empty_cart.add_item("egg", 30, 3)
    empty_cart.remove_item("egg", 10)
    assert "egg" not in empty_cart.items()

# subtotal should sum unit_price*quantity for all items

def test_subtotal_calculation(empty_cart):
    empty_cart.add_item("fig", 200, 2)
    empty_cart.add_item("grape", 50, 4)
    assert empty_cart.subtotal() == 200 * 2 + 50 * 4

# total applies bulk discount per item, shipping fee and coupon discounts correctly

def test_total_with_bulk_and_shipping(empty_cart):
    # Bulk discount triggers at quantity >=10 => 5% off each item
    empty_cart.add_item("honey", 500, 12)  # subtotal 6000
    total = empty_cart.total()
    # apply bulk discount: 6000 * 0.95 = 5700
    # shipping fee for non-member >1000? subtotal after bulk discount still >=1000 so free
    assert total == pytest.approx(5700)

# total with member gets half shipping, no bulk if quantity <10

def test_total_member_no_bulk_shipping(empty_cart):
    empty_cart.add_item("icecream", 200, 5)  # subtotal 1000 -> free shipping for non-member? actually >=1000 free
    # But let's adjust to lower subtotal to trigger fee
    empty_cart.remove_item("icecream", 1)
    empty_cart.add_item("juice", 50, 10)   # subtotal 500
    total = empty_cart.total(member=True)
    # bulk discount applies (10 units) -> 5% off subtotal 500 => 475
    # shipping fee member half of 60 => 30
    assert total == pytest.approx(475 + 30)

# Coupon discounts are applied after all other discounts

def test_total_with_coupon(empty_cart):
    empty_cart.add_item("kale", 300, 5)  # subtotal 1500 >1000 free shipping
    total = empty_cart.total(coupon="SAVE20")
    # no bulk discount because quantity <10, no shipping fee, coupon 20% => 1200
    assert total == pytest.approx(1200)

# Combined scenarios: bulk + shipping + coupon

def test_total_combined(empty_cart):
    empty_cart.add_item("lemon", 400, 15)  # subtotal 6000, bulk 5% off => 5700
    total = empty_cart.total(coupon="SAVE10")
    # apply coupon after shipping (free), so final 5700*0.9=5130
    assert total == pytest.approx(5130)

# Negative test: invalid item addition should raise ValueError

def test_add_item_invalid_price(empty_cart):
    with pytest.raises(ValueError):
        empty_cart.add_item("mango", -10, 2)

# Invalid quantity (non-positive) raises ValueError when adding or removing

def test_add_item_invalid_quantity(empty_cart):
    with pytest.raises(ValueError):
        empty_cart.add_item("nut", 25, 0)

# Removing an item that doesn't exist should not raise error

def test_remove_nonexistent_item(empty_cart):
    try:
        empty_cart.remove_item("orange", 1)
    except Exception as e:
        pytest.fail(f"remove_item raised unexpected exception {e}")
