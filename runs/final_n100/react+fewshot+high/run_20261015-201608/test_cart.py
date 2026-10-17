import pytest
import cart

# ---------- apply_discount ----------
@pytest.mark.parametrize("price,percent,expected", [
    (100.00, 0, 100.00),
    (200.00, 15, 170.00),
    (1.2345, 50, 0.62),   # 1.2345 * 0.5 = 0.61725 - rounded to 0.62
    (10.01, 30, 7.01)     # 10.01*0.7=7.007 - rounded to 7.01
])
def test_apply_discount_rounding(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price", [-1, -100])
def test_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101])
def test_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(50, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),   # boundary: quantity >= 50 -> 10
    (99, 10),
    (100, 15),
    (101, 15)
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 2.5, "ten"])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save10", 10),          # case-insensitive
    ("   SAVE20   ", 20)     # whitespace trimmed
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [None, "", "SAVEx", "XX10", "SAVE0", "SAVE51"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize("subtotal,member,expected", [
    (999.99, False, 60),
    (999.99, True, 30),
    (1000, False, 0),
    (1500, True, 0)
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -500])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart ----------
@pytest.fixture
def empty_cart():
    return cart.Cart()

def test_cart_empty(empty_cart):
    assert empty_cart.items() == {}
    assert empty_cart.subtotal() == 0
    assert empty_cart.total() == 0

def test_add_item_and_items(empty_cart):
    empty_cart.add_item("apple", 1.5, quantity=2)
    assert empty_cart.items() == {"apple": 2}

def test_add_same_item_increases_quantity(empty_cart):
    empty_cart.add_item("banana", 0.5, quantity=3)
    empty_cart.add_item("banana", 0.5, quantity=2)
    assert empty_cart.items() == {"banana": 5}

def test_add_same_item_different_price_raises(empty_cart):
    empty_cart.add_item("orange", 1.0)
    with pytest.raises(ValueError):
        empty_cart.add_item("orange", 2.0)

def test_remove_item_partial_and_complete(empty_cart):
    empty_cart.add_item("pear", 3.0, quantity=4)
    empty_cart.remove_item("pear", quantity=2)
    assert empty_cart.items() == {"pear": 2}
    # remove remaining quantity
    empty_cart.remove_item("pear", quantity=2)
    assert empty_cart.items() == {}

def test_remove_nonexistent_raises(empty_cart):
    with pytest.raises(KeyError):
        empty_cart.remove_item("nonexistent")

def test_add_item_invalid_parameters(empty_cart):
    with pytest.raises(ValueError):
        empty_cart.add_item("negprice", -1, quantity=5)
    with pytest.raises(ValueError):
        empty_cart.add_item("zeroq", 1.0, quantity=0)
    with pytest.raises(ValueError):
        empty_cart.add_item("badqty", 2.0, quantity=-3)
    with pytest.raises(ValueError):
        empty_cart.add_item("nonintqty", 1.0, quantity=2.5)

# ---------- subtotal tests ----------
def test_subtotal_bulk_discounts():
    cart_obj = cart.Cart()
    cart_obj.add_item("item1", 5.0, quantity=10)   # 10 * $5 with 5% discount
    assert cart_obj.subtotal() == 47.5

    cart_obj2 = cart.Cart()
    cart_obj2.add_item("item2", 1.2345, quantity=15)
    expected_amount = round(1.2345 * 15 * (100 - 5) / 100, 2)
    assert cart_obj2.subtotal() == expected_amount

def test_subtotal_rounding_difference():
    c = cart.Cart()
    unit_price = 0.3343333333
    qty = 3
    c.add_item("a", unit_price, quantity=qty)
    c.add_item("b", unit_price, quantity=qty)
    # According to the spec this should round only after summing:
    expected_total = round(unit_price * qty + unit_price * qty, 2)   # 2.01
    assert c.subtotal() == expected_total

# ---------- total tests ----------
def test_total_no_coupon_member_false():
    cart_obj = cart.Cart()
    cart_obj.add_item("widget", 20.0, quantity=1)
    subtotal = 20.0
    shipping = cart.shipping_fee(subtotal)
    expected_total = round(subtotal + shipping, 2)
    assert cart_obj.total(member=False) == expected_total

def test_total_with_member():
    cart_obj = cart.Cart()
    cart_obj.add_item("gadget", 25.0, quantity=1)
    subtotal = 25.0
    shipping = cart.shipping_fee(subtotal, member=True)
    expected_total = round(subtotal + shipping, 2)
    assert cart_obj.total(member=True) == expected_total

def test_total_coupon_crosses_free_shipping_threshold():
    cart_obj = cart.Cart()
    cart_obj.add_item("expensive", 1100.0, quantity=1)
    discounted_amount = cart.apply_discount(1100.0, cart.parse_coupon("SAVE10"))
    shipping = cart.shipping_fee(discounted_amount)   # member=False by default
    expected_total = round(discounted_amount + shipping, 2)
    assert cart_obj.total(coupon="SAVE10") == expected_total

def test_total_invalid_coupon_raises():
    cart_obj = cart.Cart()
    cart_obj.add_item("item", 10.0, quantity=1)
    with pytest.raises(ValueError):
        cart_obj.total(coupon="INVALID")
