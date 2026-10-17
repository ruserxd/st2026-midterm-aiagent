import pytest
import cart

# ---------- apply_discount ----------
@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),
        (101, 15, 85.85),     # 101 * 0.85 = 85.85
        (100, 0, 100.0),
        (100, 100, 0.0),
        (19.99, 33, 13.39),   # rounding to two decimals
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

def test_apply_discount_negative_price():
    with pytest.raises(ValueError):
        cart.apply_discount(-10, 5)

def test_apply_discount_percent_below_zero():
    with pytest.raises(ValueError):
        cart.apply_discount(100, -1)

def test_apply_discount_percent_above_hundred():
    with pytest.raises(ValueError):
        cart.apply_discount(100, 101)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (5, 0),
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

def test_bulk_discount_percent_invalid_negative():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-1)

def test_bulk_discount_percent_zero():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)

def test_bulk_discount_percent_non_integer():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(10.5)

# ---------- parse_coupon ----------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("SAVE1", 1),
        ("SAVE50", 50),
        ("save20", 20),
        (" SAVE30 ", 30),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "SAV10",      # wrong prefix
        "SAVE0",      # N < 1
        "SAVE51",     # N > 50
        "SAVE-5",     # negative number
        "SAVEabc",    # non-digit
        "SAVE10X",    # trailing characters
        "",           # empty string
        "   ",        # whitespace only
        "123",        # numeric but wrong format
        "savesave10", # incorrect prefix
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (999, False, 60),
        (1000, False, 0),
        (1200, False, 0),
        (800, True, 30),
        (500, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [
        -10,
        -0.5,
    ],
)
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart ----------
def test_cart_initially_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

def test_add_item_new_and_items_dict():
    c = cart.Cart()
    c.add_item('apple', 10, 2)
    assert c.items() == {'apple': 2}
    # adding the same item with same price increases quantity
    c.add_item('apple', 10, 3)
    assert c.items() == {'apple': 5}

def test_add_item_price_mismatch():
    c = cart.Cart()
    c.add_item('banana', 5, 1)
    with pytest.raises(ValueError):
        c.add_item('banana', 6, 2)

@pytest.mark.parametrize(
    "price",
    [
        -5,
        -0.01,
    ],
)
def test_add_negative_price(price):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item('pear', price, 1)

@pytest.mark.parametrize(
    "quantity",
    [0, -1, -10],
)
def test_add_nonpositive_quantity(quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item('orange', 5, quantity)

@pytest.mark.parametrize(
    "quantity",
    [2.5, 3.7],
)
def test_add_non_integer_quantity(quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item('grape', 4, quantity)

def test_remove_partial_and_full():
    c = cart.Cart()
    c.add_item('apple', 10, 5)
    # remove less than current quantity
    c.remove_item('apple', 2)
    assert c.items() == {'apple': 3}
    # remove remaining to zero
    c.remove_item('apple', 3)
    assert c.items() == {}

def test_remove_more_than_quantity_removes_item():
    c = cart.Cart()
    c.add_item('orange', 20, 1)
    c.remove_item('orange', 5)  # removing more than present
    assert 'orange' not in c.items()

def test_remove_nonexistent_raises_keyerror():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item('banana', 1)

def test_subtotal_calculation():
    c = cart.Cart()
    c.add_item('apple', 10, 2)   # subtotal 20
    c.add_item('banana', 5, 3)   # subtotal 35
    assert c.subtotal() == 35
    c.remove_item('banana', 1)
    # now banana quantity 2 -> total = 20 + 10 = 30
    assert c.subtotal() == 30

def test_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0

def test_total_no_coupon_non_member():
    c = cart.Cart()
    c.add_item('apple', 10, 2)   # 20
    c.add_item('banana', 5, 3)   # 15 -> subtotal 35
    expected_subtotal = 35
    expected_shipping = cart.shipping_fee(expected_subtotal, member=False)
    expected_total = round(expected_subtotal + expected_shipping, 2)
    assert c.total() == expected_total

def test_total_no_coupon_member():
    c = cart.Cart()
    c.add_item('apple', 10, 2)   # 20
    c.add_item('banana', 5, 3)   # 15 -> subtotal 35
    expected_subtotal = 35
    expected_shipping = cart.shipping_fee(expected_subtotal, member=True)
    expected_total = round(expected_subtotal + expected_shipping, 2)
    assert c.total(member=True) == expected_total

def test_total_with_coupon_non_member():
    c = cart.Cart()
    c.add_item('apple', 10, 2)   # 20
    c.add_item('banana', 5, 3)   # 15 -> subtotal 35
    coupon_percent = cart.parse_coupon("SAVE10")  # 10%
    discounted_amount = 35 * (1 - coupon_percent / 100)
    expected_shipping = cart.shipping_fee(discounted_amount, member=False)
    expected_total = round(discounted_amount + expected_shipping, 2)
    assert c.total(coupon="SAVE10") == expected_total

def test_total_with_coupon_member():
    c = cart.Cart()
    c.add_item('apple', 10, 2)   # 20
    c.add_item('banana', 5, 3)   # 15 -> subtotal 35
    coupon_percent = cart.parse_coupon("SAVE10")  # 10%
    discounted_amount = 35 * (1 - coupon_percent / 100)
    expected_shipping = cart.shipping_fee(discounted_amount, member=True)
    expected_total = round(discounted_amount + expected_shipping, 2)
    assert c.total(member=True, coupon="SAVE10") == expected_total

def test_total_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item('apple', 10, 1)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")

def test_shipping_fee_free_threshold_and_membership():
    # subtotal exactly at threshold
    assert cart.shipping_fee(1000, member=False) == 0
    assert cart.shipping_fee(1000, member=True) == 0

def test_total_free_shipping_after_discount():
    c = cart.Cart()
    c.add_item('expensive', 2000, 1)
    # No coupon: shipping should be free
    assert c.total() == 2000
    # Coupon that reduces to exactly 1000
    assert c.total(coupon="SAVE50") == 1000

def test_total_rounding_issue():
    c = cart.Cart()
    c.add_item('item', 11.11, 3)   # subtotal 33.33
    # Non-member with coupon 10%
    expected_subtotal = 33.33
    discounted_amount = expected_subtotal * (1 - 0.10)
    shipping_fee_nm = cart.shipping_fee(discounted_amount, member=False)
    expected_total_nm = round(discounted_amount + shipping_fee_nm, 2)
    assert c.total(coupon="SAVE10") == expected_total_nm

    # Member with same coupon
    shipping_fee_m = cart.shipping_fee(discounted_amount, member=True)
    expected_total_m = round(discounted_amount + shipping_fee_m, 2)
    assert c.total(member=True, coupon="SAVE10") == expected_total_m
