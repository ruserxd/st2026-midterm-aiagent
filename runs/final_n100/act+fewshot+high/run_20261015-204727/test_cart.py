import pytest
import cart

# ------------------------------------------------------------
# Helper functions & constants for tests
# ------------------------------------------------------------
@pytest.fixture
def new_cart():
    return cart.Cart()

# ------------------------------------------------------------
# apply_discount tests
# ------------------------------------------------------------
@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),
    (1, 33, 0.67),   # 1 * (100-33)/100 = 0.67
    (100, 0, 100.0),
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price,percent", [
    (-10, 10),
    (50, -5),
    (50, 101),
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ------------------------------------------------------------
# bulk_discount_percent tests
# ------------------------------------------------------------
@pytest.mark.parametrize("quantity,expected", [
    (5, 0),
    (10, 5),
    (50, 10),      # Expected 10 per specification
    (51, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 2.5, "a"])
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ------------------------------------------------------------
# parse_coupon tests
# ------------------------------------------------------------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    (" SAVE15 ", 15),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

def test_parse_coupon_case_insensitive():
    # Case-insensitive should be accepted per specification.
    assert cart.parse_coupon("save20") == 20

@pytest.mark.parametrize("code", [
    "DISCOUNT10",
    "SAVE-5",
    "SAVE0",
    "SAVE51",
    "",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

@pytest.mark.parametrize("code", [None, 123])
def test_parse_coupon_non_string(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ------------------------------------------------------------
# shipping_fee tests
# ------------------------------------------------------------
@pytest.mark.parametrize("subtotal,expected", [
    (500, 60),
    (999.99, 60),
    (1000, 0),
    (1500, 0),
])
def test_shipping_fee_non_member(subtotal, expected):
    assert cart.shipping_fee(subtotal) == expected

@pytest.mark.parametrize("subtotal,expected", [
    (500, 30),
    (999.99, 30),
    (1000, 0),
    (1500, 0),
])
def test_shipping_fee_member(subtotal, expected):
    assert cart.shipping_fee(subtotal, member=True) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative_subtotal(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ------------------------------------------------------------
# Cart.add_item tests
# ------------------------------------------------------------
def test_cart_add_item_success(new_cart):
    new_cart.add_item('apple', 1.0, 2)
    assert new_cart.items() == {'apple': 2}

def test_cart_add_item_negative_price(new_cart):
    with pytest.raises(ValueError):
        new_cart.add_item('banana', -5.0, 1)

@pytest.mark.parametrize("quantity", [0, -3, 1.5])
def test_cart_add_item_invalid_quantity(new_cart, quantity):
    with pytest.raises(ValueError):
        new_cart.add_item('banana', 1.0, quantity)

def test_cart_add_item_mismatched_unit_price(new_cart):
    new_cart.add_item('apple', 1.0, 2)
    with pytest.raises(ValueError):
        new_cart.add_item('apple', 1.5, 3)

# ------------------------------------------------------------
# Cart.remove_item tests
# ------------------------------------------------------------
def test_cart_remove_item_reduce_positive(new_cart):
    new_cart.add_item('orange', 0.5, 4)
    new_cart.remove_item('orange', 2)
    assert new_cart.items() == {'orange': 2}

def test_cart_remove_item_zero_quantity_removal(new_cart):
    new_cart.add_item('pear', 0.3, 3)
    new_cart.remove_item('pear', 3)   # remove all
    assert 'pear' not in new_cart.items()
    assert new_cart.subtotal() == 0

def test_cart_remove_item_over_removal(new_cart):
    new_cart.add_item('grape', 0.7, 2)
    new_cart.remove_item('grape', 5)   # remove more than present
    assert 'grape' not in new_cart.items()
    assert new_cart.subtotal() == 0

def test_cart_remove_nonexistent(new_cart):
    with pytest.raises(KeyError):
        new_cart.remove_item('nonexistent')

# ------------------------------------------------------------
# Cart.items tests
# ------------------------------------------------------------
def test_cart_items_multiple(new_cart):
    new_cart.add_item('a', 1.0, 1)
    new_cart.add_item('b', 2.0, 3)
    assert new_cart.items() == {'a': 1, 'b': 3}

# ------------------------------------------------------------
# Cart.subtotal tests
# ------------------------------------------------------------
def test_cart_subtotal_simple(new_cart):
    new_cart.add_item('widget', 10.0, 5)   # qty < 10 -> no discount
    assert new_cart.subtotal() == round(10.0 * 5, 2)

def test_cart_subtotal_bulk_discount(new_cart):
    new_cart.add_item('gadget', 20.0, 10)  # bulk discount 5%
    expected = cart.apply_discount(20.0 * 10, 5)
    assert new_cart.subtotal() == expected

def test_cart_subtotal_multiple_items(new_cart):
    new_cart.add_item('item1', 5.0, 12)   # qty >=10 <50 -> 5% discount
    new_cart.add_item('item2', 15.0, 55)  # qty >=50 <100 -> 10% discount
    line1 = cart.apply_discount(5.0 * 12, 5)
    line2 = cart.apply_discount(15.0 * 55, 10)
    expected_total = round(line1 + line2, 2)
    assert new_cart.subtotal() == expected_total

# ------------------------------------------------------------
# Cart.total tests
# ------------------------------------------------------------
def test_cart_total_empty(new_cart):
    assert new_cart.total() == 0

def test_cart_total_no_coupon_non_member_large_subtotal(new_cart):
    new_cart.add_item('expensive', 2000.0, 1)
    amount = cart.apply_discount(2000.0 * 1, 0)
    expected_total = round(amount + cart.shipping_fee(2000.0), 2)
    assert new_cart.total() == expected_total

def test_cart_total_no_coupon_non_member_small_subtotal(new_cart):
    new_cart.add_item('cheap', 500, 1)
    amount = cart.apply_discount(500 * 1, 0)
    expected_total = round(amount + cart.shipping_fee(500), 2)
    assert new_cart.total() == expected_total

def test_cart_total_member_small_subtotal(new_cart):
    new_cart.add_item('cheap', 300, 1)
    amount = cart.apply_discount(300 * 1, 0)
    fee = cart.shipping_fee(300, member=True)  # should be 30
    expected_total = round(amount + fee, 2)
    assert new_cart.total(member=True) == expected_total

def test_cart_total_coupon_no_threshold(new_cart):
    new_cart.add_item('exp', 1000.0, 1)
    amount = cart.apply_discount(1000.0 * 1, 20)
    fee = cart.shipping_fee(amount, member=False)  # shipping on discounted subtotal
    expected_total = round(amount + fee, 2)   # should be 860
    assert new_cart.total(coupon="SAVE20") == expected_total

def test_cart_total_coupon_cross_threshold_bug(new_cart):
    new_cart.add_item('exp', 1100.0, 1)
    amount = cart.apply_discount(1100.0 * 1, 10)   # discounted subtotal
    fee_expected = cart.shipping_fee(amount, member=False)
    expected_total = round(amount + fee_expected, 2)
    assert new_cart.total(coupon="SAVE10") == expected_total

def test_cart_total_invalid_coupon_raises(new_cart):
    with pytest.raises(ValueError):
        new_cart.total(coupon="INVALID")
