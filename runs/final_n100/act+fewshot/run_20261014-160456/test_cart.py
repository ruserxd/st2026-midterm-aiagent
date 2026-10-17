import pytest
import cart

# --- basic discount helpers -------------------------------------------------

def test_apply_discount_normal():
    assert cart.apply_discount(200, 15) == 170.0
    # rounding behaviour
    assert cart.apply_discount(99.999, 10) == 90.00

@pytest.mark.parametrize("price,percent", [(-1, 10), (50, -5), (50, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --- bulk discount -----------------------------------------------------------

def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

@pytest.mark.parametrize("q", [0, -1, 3.5])
def test_bulk_discount_invalid(q):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(q)

# --- coupon parsing -----------------------------------------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon("   SaVe5  ") == 5

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "SAVEXX", "INVALID", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping fee ------------------------------------------------------------

def test_shipping_fee():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(999.99) == 60

@pytest.mark.parametrize("sub", [-1, -10])
def test_shipping_fee_invalid(sub):
    with pytest.raises(ValueError):
        cart.shipping_fee(sub)

# --- Cart behaviour -----------------------------------------------------------

@pytest.fixture
def empty_cart():
    return cart.Cart()


def test_add_item_basic(empty_cart):
    empty_cart.add_item("apple", 1.0, 3)
    assert empty_cart.items() == {"apple": 3}


def test_add_same_item_increases_quantity(empty_cart):
    empty_cart.add_item("banana", 0.5, 2)
    empty_cart.add_item("banana", 0.5, 3)
    assert empty_cart.items() == {"banana": 5}


def test_add_item_wrong_price_raises(empty_cart):
    empty_cart.add_item("orange", 0.7, 1)
    with pytest.raises(ValueError):
        empty_cart.add_item("orange", 0.8, 1)

@pytest.mark.parametrize("unit,qty", [( -1, 2), (1, 0), (1, -3)])
def test_add_item_invalid(unit, qty):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("test", unit, qty)


def test_remove_item_basic(empty_cart):
    empty_cart.add_item("milk", 2.0, 4)
    empty_cart.remove_item("milk", 1)
    assert empty_cart.items() == {"milk": 3}


def test_remove_all_quantity(empty_cart):
    empty_cart.add_item("bread", 1.5, 2)
    empty_cart.remove_item("bread", 2)
    assert empty_cart.items() == {}


def test_remove_more_than_exists_raises(empty_cart):
    empty_cart.add_item("cheese", 3.0, 1)
    with pytest.raises(KeyError):
        empty_cart.remove_item("cheese", 2)


def test_subtotal_simple(empty_cart):
    empty_cart.add_item("a", 10.0, 5)   # no bulk discount
    assert empty_cart.subtotal() == 50.00


def test_subtotal_with_bulk_discount(empty_cart):
    empty_cart.add_item("b", 4.0, 12)   # 5% bulk discount
    assert empty_cart.subtotal() == round(4.0*12*(1-0.05),2)


def test_total_no_coupon_member_and_nonmember(empty_cart):
    empty_cart.add_item("x", 200.0, 3)   # subtotal 600
    # member: shipping fee should be 30 on discounted amount (600)
    assert empty_cart.total(member=True) == round(600 + 30,2)
    # non-member: shipping 60
    assert empty_cart.total() == round(600 + 60,2)


def test_total_with_coupon(empty_cart):
    empty_cart.add_item("y", 100.0, 5)   # subtotal 500, bulk none
    # coupon 10% gives 450 then shipping 60 -> total 510
    assert empty_cart.total(coupon="SAVE10") == round(450 + 60,2)


def test_total_invalid_coupon(empty_cart):
    with pytest.raises(ValueError):
        empty_cart.total(coupon="BADCODE")


def test_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0
    assert c.total(member=True) == 0
