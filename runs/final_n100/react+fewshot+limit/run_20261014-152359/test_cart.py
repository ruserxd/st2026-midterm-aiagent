import pytest
import cart

# ---------- apply_discount ---------
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# boundary checks for invalid inputs
@pytest.mark.parametrize(
    "price, percent",
    [(-1, 10), (100, -5), (100, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ---------
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (5, 0),
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

# invalid quantity
@pytest.mark.parametrize(
    "quantity",
    [0, -5, 2.5],
)
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ---------
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save25", 25),
        ("   SaVe50  ", 50),
    ],
)
def test_parse_coupon(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    ["SAVE0", "SAVE51", "abc10", "SAVEX", ""],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ---------
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, 60),
        (500, True, 30),
        (999.99, False, 60),
        (1000, False, 0),
        (2000, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-1, -100],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ---------
@pytest.fixture
def empty_cart():
    return cart.Cart()

# add_item and items
def test_add_item(empty_cart):
    empty_cart.add_item("apple", 1.0, 3)
    assert empty_cart.items() == {"apple": 3}
    # adding same item increases quantity
    empty_cart.add_item("apple", 1.0, 2)
    assert empty_cart.items() == {"apple": 5}
    # adding with different price raises ValueError
    with pytest.raises(ValueError):
        empty_cart.add_item("apple", 1.5, 1)
    # invalid unit_price or quantity
    with pytest.raises(ValueError):
        empty_cart.add_item("banana", -0.5, 2)
    with pytest.raises(ValueError):
        empty_cart.add_item("banana", 0.5, 0)

# remove_item
def test_remove_item(empty_cart):
    empty_cart.add_item("orange", 0.8, 4)
    empty_cart.remove_item("orange", 2)
    assert empty_cart.items() == {"orange": 2}
    # removing more than present removes the item
    empty_cart.remove_item("orange", 5)
    assert empty_cart.items() == {}
    with pytest.raises(KeyError):
        empty_cart.remove_item("pear", 1)

# subtotal calculation with bulk discount
def test_subtotal(empty_cart):
    empty_cart.add_item("pen", 2.0, 9)   # no bulk
    assert round(empty_cart.subtotal(), 2) == 18.0
    empty_cart.add_item("pencil", 1.5, 10)  # 5% discount on this item
    expected = round(18.0 + (1.5 * 10 * (1 - 0.05)), 2)
    assert round(empty_cart.subtotal(), 2) == expected
    # test rounding
    empty_cart.add_item("eraser", 0.333, 3)  # no bulk
    subtotal = empty_cart.subtotal()
    assert isinstance(subtotal, float)

# total with coupon and shipping
def test_total(empty_cart):
    empty_cart.add_item("book", 30.0, 1)
    # no coupon, non-member
    expected_no_coupon = round(30 + cart.shipping_fee(30, False), 2)
    assert empty_cart.total(member=False) == expected_no_coupon
    # member discount on shipping
    expected_member = round(30 + cart.shipping_fee(30, True), 2)
    assert empty_cart.total(member=True) == expected_member
    # with coupon SAVE10 (10%)
    subtotal_after_coupon = 30 * 0.9
    shipping = cart.shipping_fee(subtotal_after_coupon, False)
    total_expected = round(subtotal_after_coupon + shipping, 2)
    assert empty_cart.total(coupon="SAVE10") == total_expected
    # invalid coupon raises
    with pytest.raises(ValueError):
        empty_cart.total(coupon="BADCODE")

# empty cart costs 0 no shipping
def test_empty_cart_total():
    c = cart.Cart()
    assert c.total() == 0.0
