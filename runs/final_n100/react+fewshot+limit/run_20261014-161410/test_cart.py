import pytest
import cart

# Helper for approximate equality of floats

def approx(a, b, eps=1e-2):
    return abs(a - b) <= eps

######################
# Test standalone functions
######################

def test_apply_discount_valid():
    assert cart.apply_discount(200.0, 15) == 170.0
    assert cart.apply_discount(100.0, 0) == 100.0
    assert cart.apply_discount(50.0, 100) == 0.0

@pytest.mark.parametrize("price, percent", [(-1,10), (10,-5), (10,105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)


def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

with pytest.raises(ValueError):
    cart.bulk_discount_percent(-1)


def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon(" SAVE30 ") == 30

@pytest.mark.parametrize("code", ["",
    "SAVEXY", "ABC10", "SAVE0", "SAVE51", "save-5", "   "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)


def test_shipping_fee():
    assert cart.shipping_fee(1000) == 0.0
    assert cart.shipping_fee(999.99) == 60.0
    assert cart.shipping_fee(500, member=True) == 30.0
    assert cart.shipping_fee(0, member=False) == 60.0

with pytest.raises(ValueError):
    cart.shipping_fee(-10)

######################
# Test Cart class
######################

def test_cart_initialization():
    c = cart.Cart()
    assert isinstance(c.items(), dict)
    assert len(c.items()) == 0
    assert c.subtotal() == 0.0
    assert c.total() == 0.0


def test_add_item_and_subtotal():
    c = cart.Cart()
    c.add_item("apple", 1.00, 5)
    # bulk discount for 5 -> 0%
    assert c.subtotal() == 5.00
    c.add_item("apple", 1.00, 6)  # total quantity now 11
    # bulk discount for 11 -> 5%
    expected = (1.00 * 11) * 0.95
    assert approx(c.subtotal(), round(expected,2))

    c.add_item("banana", 0.50, 50)
    # banana gets 10% off, apple remains at 5% for qty 11
    apple = (1.00*11)*0.95
    banana = (0.50*50)*0.90
    total_expected = round(apple+banana,2)
    assert approx(c.subtotal(), total_expected)


def test_add_item_invalid():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("pear", -1, 5)
    with pytest.raises(ValueError):
        c.add_item("pear", 1, 0)
    with pytest.raises(ValueError):
        c.add_item("pear", 1, -3)

    # adding same name with different price
    c.add_item("orange", 2.00, 2)
    with pytest.raises(ValueError):
        c.add_item("orange", 3.00, 1)


def test_remove_item():
    c = cart.Cart()
    c.add_item("widget", 10, 3)
    c.remove_item("widget", 1)
    assert c.items()["widget"] == 2
    c.remove_item("widget", 2)  # should remove completely
    assert "widget" not in c.items()

    with pytest.raises(KeyError):
        c.remove_item("nonexistent", 1)


def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("gadget", 200, 5)  # subtotal 1000, no bulk discount yet
    # No coupon, not a member -> shipping fee 60
    assert approx(c.total(), round(1000+60,2))

    # Apply coupon SAVE10 (10%) and member status
    total_after_coupon = (1000 * 0.90) + 30  # shipping for members
    assert approx(c.total(member=True, coupon="SAVE10"), round(total_after_coupon,2))

    # Coupon that makes subtotal below free threshold
    c.add_item("extra", 100, 1)
    # new subtotal before coupon: 1100; after coupon 990
    total = (1100 * 0.90) + 30  # still shipping since <1000
    assert approx(c.total(member=True, coupon="SAVE10"), round(total,2))

    # No items -> total should be 0 and no shipping
    empty_cart = cart.Cart()
    assert empty_cart.total() == 0.0

# Test invalid coupon in total

def test_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("item", 10, 1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
