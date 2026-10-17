import pytest
import cart

# ---- apply_discount -------------------------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0

@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---- bulk_discount_percent ------------------------------------------

def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(1) == 0
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

@pytest.mark.parametrize("qty", [0, -3])
def test_bulk_discount_negative_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---- parse_coupon -----------------------------------------------------

def test_parse_coupon_valid_cases():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save25 ") == 25
    assert cart.parse_coupon("  SaVe50") == 50

@pytest.mark.parametrize(
    "code",
    ["", "SAVEX", "SA5", "SAVE0", "SAVE51", "ABCD10"]
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---- shipping_fee -----------------------------------------------------

def test_shipping_fee():
    assert cart.shipping_fee(999) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0
    assert cart.shipping_fee(50, member=True) == 30
    assert cart.shipping_fee(2000, member=False) == 0

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_negative_subtotal(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Cart class --------------------------------------------------------

@pytest.fixture
def empty_cart():
    return cart.Cart()


def test_add_item_new(empty_cart):
    empty_cart.add_item("apple", 1.5, 3)
    assert empty_cart.items() == {"apple": 3}


def test_add_item_increase_quantity_and_price_check():
    c = cart.Cart()
    c.add_item("banana", 0.99, 2)
    with pytest.raises(ValueError):
        # different price for same item
        c.add_item("banana", 1.09, 1)
    c.add_item("banana", 0.99, 3)
    assert c.items() == {"banana": 5}

@pytest.mark.parametrize("qty", [0, -2])
def test_add_item_invalid_quantity(qty):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("orange", 0.5, qty)

@pytest.mark.parametrize("price", [-1, -0.01])
def test_add_item_invalid_price(price):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("grape", price, 2)


def test_remove_item_basic():
    c = cart.Cart()
    c.add_item("mango", 2.0, 5)
    c.remove_item("mango", 3)
    assert c.items() == {"mango": 2}
    # removing more than remaining removes item
    c.remove_item("mango", 5)
    assert c.items() == {}

@pytest.mark.parametrize("name", ["pear", "kiwi"])
def test_remove_nonexistent(name):
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item(name, 1)

# ---- subtotal calculations --------------------------------------------

def test_subtotal_no_discount():
    c = cart.Cart()
    c.add_item("item", 10.0, 4)  # <10 => no discount
    assert c.subtotal() == 40.0


def test_subtotal_with_discounts_and_rounding():
    c = cart.Cart()
    c.add_item("socks", 5.0, 12)   # qty 12 -> 5% bulk discount
    # expected: 5*12=60 - 5% = 57.0
    assert c.subtotal() == 57.0
    c.add_item("hat", 20.0, 50)     # qty 50 ->10% discount
    # hat subtotal: 20*50=1000 -10% =900.0
    assert c.subtotal() == 957.0


def test_subtotal_rounding():
    c = cart.Cart()
    c.add_item("piece", 1.333, 3)   # no discount, 4.0 after rounding
    assert c.subtotal() == 4.0

# ---- total calculations -----------------------------------------------

def test_total_no_coupon_or_member():
    c = cart.Cart()
    c.add_item("toy", 200.0, 3)
    # subtotal: 600 - no bulk discount
    # coupon none, shipping fee 60 (subtotal <1000)
    assert c.total() == 660.0

def test_total_with_coupon_and_member():
    c = cart.Cart()
    c.add_item("book", 120.0, 10)   # qty 10 ->5% discount: 120*10=1200-60=1140
    after_discount = cart.apply_discount(1140, 20)
    expected_shipping = cart.shipping_fee(after_discount, member=True)
    assert c.total(member=True, coupon="SAVE20") == round(after_discount + expected_shipping, 2)

@pytest.mark.parametrize("code", ["BAD", "SAVEX"])
def test_total_invalid_coupon(code):
    c = cart.Cart()
    c.add_item("pen", 5.0, 1)
    with pytest.raises(ValueError):
        c.total(coupon=code)

# ---- empty cart --------------------------------------------------------

def test_empty_cart_costs_zero():
    c = cart.Cart()
    assert c.subtotal() == 0
    assert c.total() == 0
