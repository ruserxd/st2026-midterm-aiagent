import pytest
import cart

# Helper function to round for comparisons if needed

def approx(value, rel=1e-9):
    return pytest.approx(value, rel=rel)

# -------------------- tests for helper functions ---------------------------------

test_apply_discount_cases = [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
]

@pytest.mark.parametrize("price, percent, expected", test_apply_discount_cases)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == approx(expected)

# edge cases: invalid price or percent
@ pytest.mark.parametrize("price, percent", [(-1, 10), (50, -5), (50, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk discount percent
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (150, 15),
        (120, 15),
        (75, 10),
        (55, 10),
        (20, 5),
        (9, 0),
        (1, 0),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# invalid quantity
@pytest.mark.parametrize("quantity", [0, -10, 3.5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        (" save20 ", 20),
        ("SaVe50", 50),
        ("save1", 1),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "NOTA", "saver10", "SAVE-5", "   "] )
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (1000, False, 0),
        (999.99, False, 60),
        (1200, True, 0),
        (50, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# -------------------- tests for Cart class ---------------------------------

@pytest.fixture
def empty_cart():
    return cart.Cart()

# add_item basics

def test_add_new_item(empty_cart):
    empty_cart.add_item("apple", 1.5, 3)
    assert empty_cart.items() == {"apple": 3}
    assert empty_cart.subtotal() == approx(4.5)

# adding same item with same price increases quantity

def test_add_existing_item_same_price(empty_cart):
    empty_cart.add_item("banana", 2, 1)
    empty_cart.add_item("banana", 2, 2)
    assert empty_cart.items() == {"banana": 3}
    assert empty_cart.subtotal() == approx(6.0)

# adding same item with different price raises ValueError

def test_add_existing_item_diff_price(empty_cart):
    empty_cart.add_item("orange", 1, 1)
    with pytest.raises(ValueError):
        empty_cart.add_item("orange", 2, 1)

# remove_item tests

def test_remove_some_quantity(empty_cart):
    empty_cart.add_item("pear", 3, 5)
    empty_cart.remove_item("pear", 2)
    assert empty_cart.items() == {"pear": 3}
    assert empty_cart.subtotal() == approx(9.0)

# remove to zero removes item

def test_remove_to_zero(empty_cart):
    empty_cart.add_item("grape", 1, 2)
    empty_cart.remove_item("grape", 2)
    assert "grape" not in empty_cart.items()

# removing non-existent item raises KeyError

def test_remove_nonexistent(empty_cart):
    with pytest.raises(KeyError):
        empty_cart.remove_item("nonexistent", 1)

# total calculation: applies bulk discount per item, shipping and optional coupon

def test_total_basic(empty_cart):
    # add items to trigger different discounts
    empty_cart.add_item("itemA", 10, 12)   # >10 units -> 5% discount on its subtotal
    empty_cart.add_item("itemB", 20, 55)   # >50 units -> 10% discount
    # Compute expected
    subA = cart.apply_discount(10*12, 5)
    subB = cart.apply_discount(20*55, 10)
    subtotal = subA + subB
    shipping = cart.shipping_fee(subtotal)
    total_expected = subtotal + shipping
    assert empty_cart.total() == approx(total_expected)

# member discount: half shipping fee

def test_total_member_shipping(empty_cart):
    empty_cart.add_item("itemC", 100, 1)
    # subtotal=100, shipping=60 -> member gets 30
    total = empty_cart.total(member=True)
    assert total == approx(130.0)

# coupon application after discounts and shipping

def test_total_coupon(empty_cart):
    empty_cart.add_item("itemD", 200, 1)
    # no bulk discount; subtotal=200; shipping=60
    # apply coupon SAVE10 => 10% off total
    total = empty_cart.total(coupon="SAVE10")
    expected = cart.apply_discount(260.0, 10)  # 200+60=260 then 10%
    assert total == approx(expected)

# test invalid coupon raises ValueError in total

def test_total_invalid_coupon(empty_cart):
    empty_cart.add_item("itemE", 50, 1)
    with pytest.raises(ValueError):
        empty_cart.total(coupon="INVALID")
