import pytest
import cart

# Helper: compare floats with rounding as spec says

def assert_approx(value, expected):
    # Both rounded to 2 decimals
    assert round(value, 2) == round(expected, 2)

# ---- apply_discount -------------------------------------------------

test_cases_apply = [
    (200.0, 15.0, 170.0),
    (100.0, 0.0, 100.0),
    (50.0, 100.0, 0.0),
]

@pytest.mark.parametrize("price,percent,expected", test_cases_apply)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# error cases
@pytest.mark.parametrize("price,percent", [(-10, 10), (50, -5), (30, 105)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---- bulk_discount_percent -------------------------------------------
test_cases_bulk = [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
]

@pytest.mark.parametrize("quantity,expected", test_cases_bulk)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("q", [0, -1, 3.5])
def test_bulk_discount_errors(q):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(q)

# ---- parse_coupon ----------------------------------------------------
valid_coupons = {
    "SAVE10": 10,
    "save20": 20,
    "   SaVe30  ": 30,
}

@pytest.mark.parametrize("code,expected", list(valid_coupons.items()))
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

invalid_codes = ["SAVE0", "SAVE51", "NOTACODE", "SAVExx", "" ]

@pytest.mark.parametrize("code", invalid_codes)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---- shipping_fee ----------------------------------------------------
test_cases_shipping = [
    (0, 60),
    (999.99, 60),
    (1000, 0),
    (2000, 0),
]

@pytest.mark.parametrize("subtotal,expected", test_cases_shipping)
def test_shipping_fee(subtotal, expected):
    assert cart.shipping_fee(subtotal) == expected

# member pays half when not free
assert cart.shipping_fee(500, member=True) == 30

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Cart functionality ----------------------------------------------
def test_cart_add_and_items():
    c = cart.Cart()
    assert c.items() == {}
    c.add_item("apple", 1.0, 3)
    assert c.items() == {"apple": 3}
    # Adding same item increases quantity
    c.add_item("apple", 1.0, 2)
    assert c.items() == {"apple": 5}
    # Different item
    c.add_item("banana", 0.5, 10)
    assert c.items() == {"apple": 5, "banana": 10}


def test_cart_add_errors():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("pear", -1.0, 2)
    with pytest.raises(ValueError):
        c.add_item("pear", 1.0, -3)
    # price mismatch
    c.add_item("pear", 1.5, 1)
    with pytest.raises(ValueError):
        c.add_item("pear", 2.0, 1)


def test_cart_remove_and_subtotal():
    c = cart.Cart()
    c.add_item("item", 10.0, 12)   # quantity 12 -> bulk discount 5%
    # subtotal before discounts: 120
    # bulk discount 5% -> 114.0
    assert round(c.subtotal(),2) == 114.00
    # remove 2 units -> qty 10 still eligible for 5%
    c.remove_item("item", 2)
    assert round(c.subtotal(),2) == 95.0   # 100 * 0.95
    # remove 8 more -> quantity 0, item removed
    c.remove_item("item", 8)
    assert c.items() == {}
    assert c.subtotal() == 0


def test_cart_remove_errors():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent", 1)
    # remove more than present, should drop to zero and remove
    c.add_item("stuff", 5.0, 3)
    c.remove_item("stuff", 10)
    assert c.items() == {}


def test_cart_total_no_shipping_empty():
    c = cart.Cart()
    assert c.total() == 0


def test_cart_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("widget", 200.0, 10)   # bulk discount 5% -> subtotal 190
    # Apply coupon SAVE10 (10%) => 171
    total = c.total(coupon="SAVE10")
    assert round(total,2) == 231.0   # 171 + shipping 60 because not free

    # member pays half shipping
    total_member = c.total(member=True, coupon="SAVE10")
    assert round(total_member,2) == 201.0

    # no coupon, large subtotal >1000 to test free shipping
    big = cart.Cart()
    big.add_item("expensive", 600.0, 3)   # quantity 3 -> no bulk discount, subtotal 1800
    assert big.total() == 1800.0          # free shipping

# Ensure coupon parsing errors propagate in total

def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("item", 10, 1)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
