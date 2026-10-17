import pytest
import cart

# ---------------------------------------------------------------------------
# Helper functions and fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def empty_cart():
    return cart.Cart()

# ---------------------------------------------------------------------------
# apply_discount tests
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200.0, 15, 170.0),
        (100.0, 0, 100.0),
        (50.0, 100, 0.0),
        (123.45, 10, round(123.45 * 0.9, 2)),
        (0.0, 50, 0.0),
    ],
)
def test_apply_discount_basic(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price", [-1.0, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize(
    "percent",
    [-5, 101],
)
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100.0, percent)

# ---------------------------------------------------------------------------
# bulk_discount_percent tests
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------------------------------------------------------------------------
# parse_coupon tests
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save25", 25),
        ("   SaVe50   ", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "SAVE0",       # percent below allowed range
        "SAVE51",      # percent above allowed range
        "DISCOUNT10",  # wrong prefix
        None,           # not a string
        12345,          # not a string
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------------------------------------------------------------------------
# shipping_fee tests
# ---------------------------------------------------------------------------
def test_shipping_fee_negative():
    with pytest.raises(ValueError):
        cart.shipping_fee(-10.0, member=False)

@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (1000.0, False, 0),
        (1500.0, True, 0),   # free shipping regardless of membership
        (999.99, False, 60),
        (999.99, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# ---------------------------------------------------------------------------
# Cart class tests
# ---------------------------------------------------------------------------
def test_empty_cart(empty_cart):
    assert empty_cart.items() == {}
    assert empty_cart.subtotal() == 0
    assert empty_cart.total() == 0

# Adding items --------------------------------------------------------------
def test_add_item_new(empty_cart):
    cart_obj = empty_cart
    cart_obj.add_item("apple", 10.0)
    assert cart_obj.items() == {"apple": 1}

def test_add_item_existing_same_price(empty_cart):
    cart_obj = empty_cart
    cart_obj.add_item("apple", 10.0, quantity=2)
    cart_obj.add_item("apple", 10.0, quantity=3)
    assert cart_obj.items() == {"apple": 5}

def test_add_item_existing_different_price(empty_cart):
    cart_obj = empty_cart
    cart_obj.add_item("apple", 10.0)
    with pytest.raises(ValueError):
        cart_obj.add_item("apple", 12.0)

def test_add_negative_unit_price(empty_cart):
    cart_obj = empty_cart
    with pytest.raises(ValueError):
        cart_obj.add_item("banana", -5.0, quantity=1)

@pytest.mark.parametrize("quantity", [0, -3])
def test_add_non_positive_quantity(empty_cart, quantity):
    cart_obj = empty_cart
    with pytest.raises(ValueError):
        cart_obj.add_item("orange", 2.0, quantity=quantity)

def test_add_non_int_quantity(empty_cart):
    cart_obj = empty_cart
    with pytest.raises(ValueError):
        cart_obj.add_item("pear", 3.5, quantity="two")

# Removing items --------------------------------------------------------------
def test_remove_item_not_in_cart():
    cart_obj = cart.Cart()
    with pytest.raises(KeyError):
        cart_obj.remove_item("apple")

def test_remove_partial(empty_cart):
    cart_obj = empty_cart
    cart_obj.add_item("book", 12.0, quantity=3)
    cart_obj.remove_item("book", quantity=1)
    assert cart_obj.items() == {"book": 2}

def test_remove_full_and_check_subtotal(empty_cart):
    cart_obj = empty_cart
    cart_obj.add_item("book", 12.0, quantity=2)
    cart_obj.remove_item("book", quantity=2)  # should remove item completely
    assert cart_obj.items() == {}
    assert cart_obj.subtotal() == 0
    assert cart_obj.total() == 0

# Items dict immutability ---------------------------------------------
def test_items_dict_immutable(empty_cart):
    cart_obj = empty_cart
    cart_obj.add_item("apple", 1.0, quantity=2)
    items_copy = cart_obj.items()
    items_copy["apple"] = 99  # modify copy
    assert cart_obj.items() == {"apple": 2}

# Subtotal bulk discount -----------------------------------------------------
def test_cart_subtotal_bulk_discounts(empty_cart):
    cart_obj = empty_cart
    cart_obj.add_item("apple", 10.0, quantity=12)   # 5% discount
    cart_obj.add_item("banana", 20.0, quantity=55)  # 10% discount
    expected_subtotal = round(120 * (1 - 0.05), 2) + round(1100 * (1 - 0.10), 2)
    assert cart_obj.subtotal() == expected_subtotal

# Total calculations ----------------------------------------------------------
def test_cart_total_no_coupon_non_member(empty_cart):
    cart_obj = empty_cart
    cart_obj.add_item("apple", 30.0, quantity=10)  # subtotal 285
    expected_total = round(285 + 60, 2)
    assert cart_obj.total() == expected_total

def test_cart_total_no_coupon_member(empty_cart):
    cart_obj = empty_cart
    cart_obj.add_item("apple", 30.0, quantity=10)  # subtotal 285
    expected_total = round(285 + 30, 2)
    assert cart_obj.total(member=True) == expected_total

# Total with coupon that changes shipping eligibility ---------------------------------
def test_cart_total_with_coupon_threshold_bug(empty_cart):
    cart_obj = empty_cart
    # Subtotal >=1000 before discount
    cart_obj.add_item("expensive", 200.0, quantity=6)  # subtotal 1200 (no bulk)
    expected_after_discount = round(1200 * (1 - 0.25), 2)  # 900.0
    expected_total = round(expected_after_discount + 60, 2)   # shipping on discounted amount
    assert cart_obj.total(coupon="SAVE25") == expected_total

def test_cart_total_with_coupon_member_threshold_bug(empty_cart):
    cart_obj = empty_cart
    cart_obj.add_item("expensive", 200.0, quantity=6)
    expected_after_discount = round(1200 * (1 - 0.25), 2)   # 900.0
    expected_total = round(expected_after_discount + 30, 2)   # member shipping on discounted amount
    assert cart_obj.total(member=True, coupon="SAVE25") == expected_total
