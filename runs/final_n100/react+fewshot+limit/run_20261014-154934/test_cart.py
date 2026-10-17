import pytest
import cart

# ---------- Utility helpers for tests ----------

def approx_equal(a, b, eps=1e-9):
    return abs(a - b) < eps

# ---------- Tests for standalone functions ----------

@pytest.mark.parametrize("price,percent,expected", [
    (200.0, 15, 170.0),        # example from spec
    (100.0, 0, 100.0),         # no discount
    (50.0, 100, 0.0),          # full discount
])
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == pytest.approx(expected)

@pytest.mark.parametrize("price", [ -1.0, -0.01 ])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [ -5, 101, 200])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100.0, percent)

# bulk discount percent
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 1.5, "10" ])
def test_bulk_discount_invalid_quantity_raises(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    ("   SaVe5  ", 5),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [ "SAVE0", "SAVE51", "SAVExx", "ABC10", "save" ])
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee
@pytest.mark.parametrize("subtotal,member,expected", [
    (0.0, False, 60),
    (500.0, True, 30),
    (1000.0, False, 0),
    (2000.0, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member=member) == expected

@pytest.mark.parametrize("subtotal", [ -1.0, -100 ])
def test_shipping_fee_negative_subtotal_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Tests for Cart class ----------

def test_cart_initial_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 0.0


def test_add_item_basic_and_bulk_discount():
    c = cart.Cart()
    c.add_item("apple", 1.00, quantity=5)
    # subtotal should be 5 * 1.00 = 5.00 (no bulk discount)
    assert c.subtotal() == pytest.approx(5.0)

    c.add_item("banana", 2.00, quantity=10)  # triggers 5% bulk
    # banana subtotal: 20 - 5% = 19.0
    expected = 5.0 + 19.0
    assert c.subtotal() == pytest.approx(expected)

    # items mapping
    assert c.items() == {"apple": 5, "banana": 10}


def test_add_item_existing_increase_and_price_check():
    c = cart.Cart()
    c.add_item("soda", 1.50, quantity=3)
    # adding more same item with same price
    c.add_item("SODA", 1.50, quantity=2)  # case-sensitive name; spec says name used as key
    assert c.items() == {"soda": 5}

    # now attempt to add same name but different price -> should raise ValueError
    with pytest.raises(ValueError):
        c.add_item("soda", 2.00, quantity=1)


def test_add_item_invalid_params():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("pen", -1.0, quantity=1)   # negative price
    with pytest.raises(ValueError):
        c.add_item("pen", 0.5, quantity=-3)   # negative quantity
    with pytest.raises(ValueError):
        c.add_item("pen", 0.5, quantity=0)     # zero quantity


def test_remove_item_basic_and_removal_when_zero():
    c = cart.Cart()
    c.add_item("book", 10.0, quantity=4)
    c.remove_item("book", quantity=2)
    assert c.items() == {"book": 2}

    # remove remaining quantity => item removed
    c.remove_item("book", quantity=2)
    assert c.items() == {}


def test_remove_nonexistent_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent", quantity=1)


def test_total_no_coupon_or_member():
    c = cart.Cart()
    c.add_item("toy", 50.0, quantity=3)   # subtotal: 150 -> no bulk discount
    total = c.total(member=False)
    # shipping fee 60 applied to subtotal after coupon (none)
    expected_total = 150 + 60
    assert total == pytest.approx(expected_total)


def test_total_with_coupon_and_member():
    c = cart.Cart()
    c.add_item("shirt", 200.0, quantity=10)  # triggers 5% bulk: 2000 - 100 = 1900
    # apply coupon SAVE20 (20%) -> subtotal becomes 1520
    total = c.total(member=True, coupon="SAVE20")
    # shipping fee after coupon: subtotal 1520 >= 1000 => free
    expected_total = 1520
    assert total == pytest.approx(expected_total)


def test_total_coupon_invalid_raises():
    c = cart.Cart()
    c.add_item("shirt", 50.0, quantity=1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# ---------- End of tests ----------
