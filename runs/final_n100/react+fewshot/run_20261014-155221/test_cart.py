import pytest
import cart

# Helper to format expected roundings

def r(x): return round(x,2)

###########################
# apply_discount tests    
###########################

@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),           # example from spec
        (100, 0, 100.0),            # no discount
        (50, 100, 0.0),             # full discount
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == r(expected)

# invalid price or percent
@pytest.mark.parametrize(
    "price, percent",
    [(-1, 10), (100, -5), (100, 105)],
)
def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

###########################
# bulk_discount_percent   
###########################

@pytest.mark.parametrize(
    "quantity, expected",
    [
        (5, 0),      # less than 10
        (10, 5),     # >=10 but <50
        (50, 10),    # >=50 but <100
        (150, 15),   # >=100
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# invalid quantity
@pytest.mark.parametrize("quantity", [0, -5, 3.2])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

###########################
# parse_coupon            
###########################

@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        (" SAVE30 ", 30),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["", "ABC10", "SAVE0", "SAVE51", "SAVE-5", "SAVEX"] )
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

###########################
# shipping_fee            
###########################

@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, 60),      # base fee
        (999.99, True, 30),   # half for members below threshold
        (1000, False, 0),     # free shipping at threshold
        (1500, True, 0),      # still free after member discount
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# invalid subtotal
@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

###########################
# Cart class              
###########################

@pytest.fixture
def empty_cart():
    return cart.Cart()

# items dict

def test_cart_items_empty(empty_cart):
    assert empty_cart.items() == {}

# add_item: basic addition

def test_cart_add_basic(empty_cart):
    empty_cart.add_item("apple", 0.5, 4)
    assert empty_cart.items() == {"apple": 4}
    # subtotal should be 2.00 (no bulk discount yet)
    assert r(empty_cart.subtotal()) == 2.0

# add same item increases quantity, price must match

def test_cart_add_same_item_price_mismatch(empty_cart):
    empty_cart.add_item("banana", 1.0, 3)
    with pytest.raises(ValueError):
        empty_cart.add_item("banana", 1.2, 2)

# bulk discount applied in subtotal

def test_cart_bulk_discount(empty_cart):
    # 10 units => 5% discount on that item
    empty_cart.add_item("item", 20.0, 10)  # base 200
    assert r(empty_cart.subtotal()) == r(200 * (1 - 0.05))

# remove_item: reduces quantity and removes when zero

def test_cart_remove_partial_and_full(empty_cart):
    empty_cart.add_item("orange", 3.0, 5)
    empty_cart.remove_item("orange", 2)
    assert empty_cart.items() == {"orange": 3}
    empty_cart.remove_item("orange", 3)  # should remove item
    assert empty_cart.items() == {}

# removing non-existent raises KeyError

def test_cart_remove_nonexistent(empty_cart):
    with pytest.raises(KeyError):
        empty_cart.remove_item("pear", 1)

# total without coupon or member: subtotal + shipping (if any)

def test_cart_total_no_coupon_member(empty_cart):
    empty_cart.add_item("widget", 100.0, 2)  # 200 subtotal
    assert r(empty_cart.total()) == r(200 + 60)   # shipping fee for non-member

# total with coupon and member: order of operations matters

def test_cart_total_coupon_member(empty_cart):
    empty_cart.add_item("gadget", 250.0, 1)
    # subtotal 250 -> apply 10% coupon => 225
    # shipping fee on 225 for non-member is 60
    assert r(empty_cart.total(coupon="SAVE10")) == r(225 + 60)

# member discount halves shipping after coupon

def test_cart_total_member_shipping(empty_cart):
    empty_cart.add_item("large", 2000.0, 1)  # subtotal 2000 >1000 => free
    assert r(empty_cart.total(member=True)) == 2000.0

# empty cart cost zero

def test_cart_total_empty(empty_cart):
    assert empty_cart.total() == 0.0
