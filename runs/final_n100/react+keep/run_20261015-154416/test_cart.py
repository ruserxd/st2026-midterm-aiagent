import pytest
import cart

# ---------- function apply_discount ---------------------------------

def test_apply_discount_normal():
    assert cart.apply_discount(200, 15) == 170.0
    # round to two decimals
    assert cart.apply_discount(199, 10) == 179.1

@pytest.mark.parametrize("price", [-10, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 20)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- function bulk_discount_percent --------------------------

def test_bulk_discount_percent_levels():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@pytest.mark.parametrize("qty", [0, -1])
def test_bulk_discount_invalid_quantity(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- function parse_coupon ----------------------------------

def test_parse_coupon_valid_cases():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon(" save20 ") == 20
    assert cart.parse_coupon("Save5") == 5

@pytest.mark.parametrize("code", ["save51", "XYZ", "", "SAVE-10"])
def test_parse_coupon_invalid_cases(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- function shipping_fee -----------------------------------

def test_shipping_fee_basic():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0
    # below threshold
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(0) == 60

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class --------------------------------------------

@pytest.fixture
def empty_cart():
    return cart.Cart()

# Adding items

def test_add_item_new(empty_cart):
    empty_cart.add_item("apple", 100, 2)
    assert empty_cart.items() == {"apple": 2}
    # subtotal should include bulk discount if applicable
    assert empty_cart.subtotal() == 200.0

def test_add_item_increase_quantity(empty_cart):
    empty_cart.add_item("banana", 50, 3)
    empty_cart.add_item("banana", 50, 2)
    assert empty_cart.items()["banana"] == 5
    # bulk discount for quantity=5 -> 0%
    assert empty_cart.subtotal() == 250.0


def test_add_item_price_mismatch(empty_cart):
    empty_cart.add_item("orange", 30, 1)
    with pytest.raises(ValueError):
        empty_cart.add_item("orange", 35, 2)

# Removing items

def test_remove_item_reduce_quantity(empty_cart):
    empty_cart.add_item("mango", 80, 4)
    empty_cart.remove_item("mango", 1)
    assert empty_cart.items()["mango"] == 3
    # subtotal after bulk discount for quantity=3 -> 0%
    assert empty_cart.subtotal() == 240.0

def test_remove_item_zero_quantity(empty_cart):
    empty_cart.add_item("peach", 60, 1)
    empty_cart.remove_item("peach", 1)
    assert "peach" not in empty_cart.items()
    assert empty_cart.subtotal() == 0.0

@pytest.mark.parametrize("name", ["nonexistent"])
def test_remove_nonexistent(empty_cart, name):
    with pytest.raises(KeyError):
        empty_cart.remove_item(name, 1)

# subtotal bulk discount effect

def test_subtotal_bulk_discount():
    cart_obj = cart.Cart()
    cart_obj.add_item("itemA", 200, 10)   # 5% discount on this line
    cart_obj.add_item("itemB", 100, 50)   # 10% discount
    # Calculate expected: 200*10=2000 -> 5% => 1900; 100*50=5000 -> 10% => 4500; sum=6400
    assert cart_obj.subtotal() == 6400.0

# total with coupon and shipping

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("widget", 100, 20)   # 10% bulk discount -> line=2000*90%=1800
    # subtotal after bulk: 1800
    # apply coupon SAVE20 => 20% off subtotal -> 1440
    total = c.total(coupon="SAVE20")
    # shipping fee for amount 1440 >=1000 so free
    assert total == 1440.0

# empty cart costs zero

def test_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0

# member discount on shipping only applied after coupon

def test_shipping_member_effect_on_coupon_amount():
    c = cart.Cart()
    c.add_item("gadget", 50, 1)   # no bulk discount
    total_member = c.total(member=True)
    # subtotal=50; coupon none -> 50; shipping for 50 non-member? Wait member flag is passed to Cart.total.
    # shipping fee based on amount after coupon: subtotal 50 => shipping 60, member pays 30
    assert total_member == 80.0
    total_nonmember = c.total(member=False)
    assert total_nonmember == 110.0

# coupon case sensitivity and whitespace

def test_coupon_case_and_whitespace(empty_cart):
    empty_cart.add_item("item", 100, 1)
    assert empty_cart.total(coupon=" SAVE10 ") == 90.0
