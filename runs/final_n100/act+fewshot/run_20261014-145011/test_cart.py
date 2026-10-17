import pytest
import cart

# ---------- helper fixtures ----------
@pytest.fixture
def empty_cart():
    return cart.Cart()

# ---------- apply_discount tests ----------
@pytest.mark.parametrize("price,percent,result", [
    (200.0, 15, 170.0),      # normal case
    (100.0, 0, 100.0),       # zero percent
    (50.0, 100, 0.0),        # full discount
])
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [
    (-1, 10),                # negative price
    (100, -5),               # negative percent
    (100, 105),              # percent > 100
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent tests ----------
@pytest.mark.parametrize("quantity,expected", [
    (1, 0),          # below 10
    (9, 0),          # just below 10
    (10, 5),         # start of 5%
    (49, 5),         # just before 50
    (50, 10),        # start of 10%
    (99, 10),        # just before 100
    (100, 15),       # start of 15%
    (200, 15),       # above 100
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5, 1.2])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon tests ----------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    ("  SaVe30  ", 30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVE0",          # N < 1
    "SAVE51",         # N > 50
    "DISCOUNT10",    # wrong prefix
    "SAVE-5",         # negative
    "SAVEX",          # non-digit
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee tests ----------
@pytest.mark.parametrize("subtotal,member,expected", [
    (0, False, 60),
    (500, True, 30),
    (1000, False, 0),
    (1200, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart tests ----------

def test_cart_init_and_items(empty_cart):
    assert empty_cart.items() == {}


def test_add_item_new(empty_cart):
    empty_cart.add_item("apple", 2.0, 3)
    assert empty_cart.items() == {"apple": 3}


def test_add_item_existing_same_price(empty_cart):
    empty_cart.add_item("banana", 1.5, 2)
    empty_cart.add_item("banana", 1.5, 4)
    assert empty_cart.items() == {"banana": 6}


def test_add_item_same_name_diff_price_raises(empty_cart):
    empty_cart.add_item("orange", 3.0, 1)
    with pytest.raises(ValueError):
        empty_cart.add_item("orange", 2.5, 1)


def test_remove_item_partial_and_complete(empty_cart):
    empty_cart.add_item("cherry", 0.75, 10)
    # remove fewer than existing
    empty_cart.remove_item("cherry", 3)
    assert empty_cart.items() == {"cherry": 7}
    # remove remaining quantity
    empty_cart.remove_item("cherry", 7)
    assert empty_cart.items() == {}


def test_remove_nonexistent_raises(empty_cart):
    with pytest.raises(KeyError):
        empty_cart.remove_item("nonexist", 1)

# ---------- subtotal calculation ----------

def test_subtotal_with_bulk_discount():
    c = cart.Cart()
    # 12 apples, bulk discount 5%
    c.add_item("apple", 10.0, 12)   # unit price 10
    # 55 oranges, bulk discount 10%
    c.add_item("orange", 20.0, 55)
    expected = (
        (10.0 * 12) * 0.95 +   # 5% off apples
        (20.0 * 55) * 0.90     # 10% off oranges
    )
    assert c.subtotal() == round(expected, 2)

# ---------- total calculation ----------

def test_total_no_coupon_member():
    c = cart.Cart()
    c.add_item("item", 200.0, 1)   # subtotal 200
    expected_sub = 200.0
    # no coupon: use subtotal directly
    shipping = cart.shipping_fee(expected_sub, member=True)
    total_expected = round(expected_sub + shipping, 2)
    assert c.total(member=True) == total_expected


def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("item", 100.0, 1)   # subtotal 100
    # coupon SAVE10 => 10% off
    discounted_sub = cart.apply_discount(100.0, 10)
    shipping = cart.shipping_fee(discounted_sub, member=False)
    total_expected = round(discounted_sub + shipping, 2)
    assert c.total(coupon="SAVE10") == total_expected


def test_total_invalid_coupon_raises(empty_cart):
    with pytest.raises(ValueError):
        empty_cart.total(coupon="BADCODE")

# ---------- empty cart total is zero ----------

def test_empty_cart_total_is_zero():
    c = cart.Cart()
    assert c.total() == 0.0
