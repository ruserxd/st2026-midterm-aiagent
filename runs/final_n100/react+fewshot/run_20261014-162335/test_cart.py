import pytest
import cart

# ---- apply_discount -----------------------------------------------------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.00),
    (100, 0, 100.00),
    (50, 100, 0.00),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# invalid price
@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_invalid_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)
# invalid percent
@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---- bulk_discount_percent ----------------------------------------------
@pytest.mark.parametrize("quantity,expected", [
    (5, 0),
    (10, 5),
    (20, 5),
    (50, 10),
    (75, 10),
    (100, 15),
    (200, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -3])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---- parse_coupon -------------------------------------------------------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save25", 25),
    ("  SaVe50 ", 50),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "INVALID"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---- shipping_fee -------------------------------------------------------
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (999.99, False, 60),
    (1000, False, 0),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Cart ---------------------------------------------------------------
@pytest.fixture
def empty_cart():
    return cart.Cart()

# test initialization

def test_empty_cart_initializes(empty_cart):
    assert isinstance(empty_cart.items(), dict) and len(empty_cart.items()) == 0

# add_item

def test_add_single_item(empty_cart):
    empty_cart.add_item("Apple", 1.00)
    assert empty_cart.items() == {"Apple": 1}

# adding same item increments quantity and requires same unit price

def test_add_same_item_increments_quantity_and_valid_price(empty_cart):
    empty_cart.add_item("Banana", 0.5, 2)
    empty_cart.add_item("Banana", 0.5, 3)
    assert empty_cart.items() == {"Banana": 5}

# price/quantity validation in add_item
@pytest.mark.parametrize("price,qty", [(-1, 1), (1, 0)])
def test_add_item_invalid_price_qty(empty_cart, price, qty):
    with pytest.raises(ValueError):
        empty_cart.add_item("Orange", price, qty)

# price mismatch raises ValueError

def test_add_item_price_mismatch(empty_cart):
    empty_cart.add_item("Pear", 2.0, 1)
    with pytest.raises(ValueError):
        empty_cart.add_item("Pear", 3.0, 1)

# remove_item

def test_remove_items_and_auto_removal(empty_cart):
    empty_cart.add_item("Grape", 2.0, 4)
    empty_cart.remove_item("Grape", 2)
    assert empty_cart.items() == {"Grape": 2}
    empty_cart.remove_item("Grape", 2)  # quantity reaches zero
    assert "Grape" not in empty_cart.items()

# removing non-existent item raises KeyError

def test_remove_nonexistent(empty_cart):
    with pytest.raises(KeyError):
        empty_cart.remove_item("Nonexistent", 1)

# subtotal calculations with bulk discount

def test_subtotal_bulk_discount(empty_cart):
    # 10 Apples at $1 each - 5% discount on all 10 units
    empty_cart.add_item("Apple", 1.00, 10)
    expected = cart.apply_discount(10 * 1.0, 5)
    assert pytest.approx(expected, rel=1e-6) == empty_cart.subtotal()

# subtotal zero for empty cart

def test_subtotal_empty(empty_cart):
    assert empty_cart.subtotal() == 0.00

# total with coupon and shipping

def test_total_with_coupon_and_shipping(empty_cart):
    # 20 Bananas at $1 each - bulk discount 5%
    empty_cart.add_item("Banana", 1.0, 20)
    # subtotal: 20 * 1 = 20, 5% off => 19
    assert pytest.approx(19.00, rel=1e-6) == empty_cart.subtotal()
    # apply coupon SAVE10 - 10% off of 19 => 17.1
    total_with_coupon = empty_cart.total(coupon="SAVE10")
    assert pytest.approx(17.10, rel=1e-6) == total_with_coupon
    # shipping: subtotal after coupon is 17.1 (<1000) -> 60 fee
    assert cart.shipping_fee(17.10) == 60
    # final total includes shipping => 77.10
    assert pytest.approx(77.10, rel=1e-6) == empty_cart.total(coupon="SAVE10")

# member discount reduces shipping fee by half

def test_member_ships_lesser(empty_cart):
    empty_cart.add_item("Item", 5.0, 3)  # subtotal 15
    total = empty_cart.total(member=True)
    assert cart.shipping_fee(15, True) == 30
    assert pytest.approx(45.0, rel=1e-6) == total

# empty cart no shipping fee and total 0

def test_total_empty_cart(empty_cart):
    assert empty_cart.total() == 0.00
