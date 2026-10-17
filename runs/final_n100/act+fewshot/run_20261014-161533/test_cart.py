import pytest
import cart

# Helper to round as per spec (already internal)

@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price, percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (1, 0),
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 3.2])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(int(quantity)) if isinstance(quantity,int) else cart.bulk_discount_percent(quantity)

# parse_coupon tests
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

@pytest.mark.parametrize("code", ["SAVEE10", "SAVE0", "SAVE51", "ABC10", ""] )
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (999.99, False, 60),
        (1000, False, 0),
        (1200, True, 0),
        (500, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -50])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart tests
@pytest.fixture
def empty_cart():
    return cart.Cart()

def test_add_item_new(empty_cart):
    c = empty_cart
    c.add_item("apple", 1.0, 3)
    assert c.items() == {"apple": 3}

def test_add_item_existing_same_price(empty_cart):
    c = empty_cart
    c.add_item("banana", 2.5, 2)
    c.add_item("banana", 2.5, 1)
    assert c.items() == {"banana": 3}

def test_add_item_existing_diff_price(empty_cart):
    c = empty_cart
    c.add_item("orange", 0.5, 1)
    with pytest.raises(ValueError):
        c.add_item("orange", 0.6, 2)

@pytest.mark.parametrize("quantity", [0, -3])
def test_add_item_invalid_quantity(empty_cart, quantity):
    with pytest.raises(ValueError):
        empty_cart.add_item("pear", 1.0, quantity)

@pytest.mark.parametrize("price", [-1.0, 2.5])
def test_add_item_price_validation(empty_cart, price):
    if price < 0:
        with pytest.raises(ValueError):
            empty_cart.add_item("pear", price, 1)
    else:
        # valid case
        empty_cart.add_item("pear", price, 1)
        assert "pear" in empty_cart.items()

# remove_item tests
def test_remove_partial(empty_cart):
    c = empty_cart
    c.add_item("mango", 3.0, 5)
    c.remove_item("mango", 2)
    assert c.items() == {"mango": 3}

def test_remove_entire_and_more(empty_cart):
    c = empty_cart
    c.add_item("peach", 4.0, 2)
    c.remove_item("peach", 3)  # should remove completely
    assert "peach" not in c.items()

def test_remove_nonexistent(empty_cart):
    with pytest.raises(KeyError):
        empty_cart.remove_item("nonexist", 1)

# subtotal tests
@pytest.mark.parametrize(
    "setup, expected",
    [
        ([], 0.0),
        ([("item", 100.0, 9)], 900.0),
        ([("item", 100.0, 10)], 950.0),  # 5% bulk discount
        ([("a", 50.0, 49)], 50*49 - (5/100)*50*49),
    ],
)
def test_subtotal(setup, expected):
    c = cart.Cart()
    for name, price, qty in setup:
        c.add_item(name, price, qty)
    assert c.subtotal() == round(expected, 2)

# total tests with coupon and shipping
@pytest.mark.parametrize(
    "items, coupon, member, expected",
    [
        # no items -> 0
        ([], None, False, 0.0),
        # simple case: one item, no bulk, no coupon, non-member
        ([("book", 30.0, 2)], None, False, 60 + 60),  # subtotal 60, shipping 60
        # with coupon reducing 10%
        ([("pen", 5.0, 20)], "SAVE10", False, 80 - 8 + 60),
        # member pays half shipping
        ([("lamp", 200.0, 1)], None, True, 200 + 30),
    ],
)
def test_total(items, coupon, member, expected):
    c = cart.Cart()
    for name, price, qty in items:
        c.add_item(name, price, qty)
    assert c.total(member=member, coupon=coupon) == round(expected, 2)

# total invalid coupon
def test_total_invalid_coupon(empty_cart):
    with pytest.raises(ValueError):
        empty_cart.total(coupon="BAD")
