import pytest
import cart

@pytest.fixture
def empty_cart():
    return cart.Cart()

# apply_discount tests
def test_apply_discount_normal():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize(("price", "percent", "expected"), [
    (19.99, 10, 17.99),
    (99.99, 5, 94.99),
])
def test_apply_discount_rounding(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

def test_apply_discount_errors():
    with pytest.raises(ValueError):
        cart.apply_discount(-5, 10)
    with pytest.raises(ValueError):
        cart.apply_discount(100, -1)
    with pytest.raises(ValueError):
        cart.apply_discount(100, 101)

# bulk_discount_percent tests
@pytest.mark.parametrize(("quantity", "expected"), [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent_thresholds(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1])
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize(("code", "expected"), [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("invalid_code", [
    "DISCOUNT10",
    "SAVE0",
    "SAVE51",
    "SAVEX",
])
def test_parse_coupon_invalid(invalid_code):
    with pytest.raises(ValueError):
        cart.parse_coupon(invalid_code)

# shipping_fee tests
@pytest.mark.parametrize(("subtotal", "member", "expected"), [
    (1000, False, 0),
    (1500, False, 0),
    (999, False, 60),
    (999, True, 30),
    (1000, True, 0),
    (0, False, 60),
    (0, True, 30)
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

@pytest.mark.parametrize("negative", [-1])
def test_shipping_fee_errors(negative):
    with pytest.raises(ValueError):
        cart.shipping_fee(negative)

# Cart tests
def test_cart_empty(empty_cart):
    assert empty_cart.items() == {}
    assert empty_cart.subtotal() == 0.0
    assert empty_cart.total() == 0.0

def test_cart_add_item(empty_cart):
    empty_cart.add_item("apple", 5, 2)
    assert empty_cart.items() == {"apple": 2}
    empty_cart.add_item("apple", 5, 3)
    assert empty_cart.items() == {"apple": 5}

def test_cart_add_existing_diff_price(empty_cart):
    empty_cart.add_item("banana", 10, 1)
    with pytest.raises(ValueError):
        empty_cart.add_item("banana", 12, 2)

@pytest.mark.parametrize(("name", "unit_price", "quantity"), [
    ("orange", -5, 1),
    ("orange", 5, 0),
])
def test_cart_add_invalid_parameters(empty_cart, name, unit_price, quantity):
    with pytest.raises(ValueError):
        empty_cart.add_item(name, unit_price, quantity)

def test_cart_remove_item_partial():
    c = cart.Cart()
    c.add_item("apple", 2, 3)
    c.remove_item("apple", 1)
    assert c.items() == {"apple": 2}
    c.remove_item("apple", 2)
    assert c.items() == {}

def test_cart_remove_item_more_than_quantity():
    c = cart.Cart()
    c.add_item("apple", 2, 3)
    c.remove_item("apple", 5)  # remove more than available
    assert c.items() == {}

def test_cart_remove_missing():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent", 1)

def test_cart_items_returns_copy(empty_cart):
    empty_cart.add_item("pear", 3, 4)
    items_dict = empty_cart.items()
    items_dict["pear"] = 10
    assert empty_cart.items() == {"pear": 4}

def test_cart_subtotal_no_bulk():
    c = cart.Cart()
    c.add_item("item", 20, 1)
    assert c.subtotal() == 20.0

def test_cart_subtotal_with_discounts():
    c = cart.Cart()
    # quantity 12 -> bulk discount 5%
    c.add_item("banana", 20, 12)   # 240 * .95 = 228
    # quantity 10 -> bulk discount 5%
    c.add_item("apple", 10, 10)    # 100 * .95 = 95
    expected_subtotal = round(228 + 95, 2)
    assert c.subtotal() == expected_subtotal

def test_cart_total_basic():
    c = cart.Cart()
    c.add_item("item", 10, 1)
    assert c.total() == 70.0
    assert c.total(member=True) == 40.0

@pytest.mark.parametrize(("subtotal", "coupon", "member", "expected"), [
    (200, "SAVE10", False, 240.0),
    (200, "SAVE10", True, 210.0),
])
def test_cart_total_with_coupon_and_member(subtotal, coupon, member, expected):
    c = cart.Cart()
    c.add_item("item", subtotal, 1)
    assert c.total(coupon=coupon, member=member) == expected

def test_cart_total_shipping_free():
    c = cart.Cart()
    c.add_item("expensive", 1500, 1)
    assert c.total() == 1500.0

@pytest.mark.parametrize(("subtotal", "coupon", "expected"), [
    (2000, "SAVE50", 1000.0),
    (1500, "SAVE20", 1200.0),
])
def test_cart_total_shipping_free_after_coupon(subtotal, coupon, expected):
    c = cart.Cart()
    c.add_item("item", subtotal, 1)
    assert c.total(coupon=coupon) == expected

@pytest.mark.parametrize(("unit_price", "coupon", "member", "expected"), [
    (19.99, "SAVE15", False, 76.99),
    (19.99, "SAVE15", True, 46.99),
])
def test_cart_total_rounding_with_coupon_and_shipping(unit_price, coupon, member, expected):
    c = cart.Cart()
    c.add_item("item", unit_price, 1)
    assert c.total(coupon=coupon, member=member) == expected

@pytest.mark.parametrize(("subtotal", "coupon", "member", "expected"), [
    (1500, "SAVE50", False, 810.0),
    (1500, "SAVE50", True, 780.0),
])
def test_cart_total_shipping_applies_after_large_discount(subtotal, coupon, member, expected):
    c = cart.Cart()
    c.add_item("item", subtotal, 1)
    assert c.total(coupon=coupon, member=member) == expected

def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("item", 10, 1)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
