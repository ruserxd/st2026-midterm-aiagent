import pytest
import cart

# --- apply_discount -------------------------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0

# rounding check – round to two decimals
assert cart.apply_discount(99.99, 10) == round(99.99 * 0.9, 2)

@pytest.mark.parametrize("price",[-1,-0.01])
def test_apply_discount_invalid_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent",[-5,101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# --- bulk_discount_percent --------------------------------------------

@pytest.mark.parametrize(
    "quantity,expected",
    [(9,0),(10,5),(49,5),(50,10),(99,10),(100,15),(150,15)],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity",[0,-1])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --- parse_coupon -----------------------------------------------------

@pytest.mark.parametrize(
    "code,expected",
    ["SAVE10", 10],
    ["save20", 20],
    ["  SAVE30 ", 30],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code",["SAVEXX","SAVe0","sava1","NOPE10","SAVE51","   "])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee -----------------------------------------------------

@pytest.mark.parametrize(
    "subtotal,member,expected",
    [(999, False, 60), (1000, False, 0), (5000, True, 30)],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal",[-1,-10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --- Cart class --------------------------------------------------------

def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item("apple", 0.5, 3)
    assert c.items() == [("apple", 0.5, 3)]
    # adding same item increases quantity
    c.add_item("apple", 0.5, 2)
    assert c.items() == [("apple", 0.5, 5)]

# adding with mismatched price raises ValueError
@pytest.mark.parametrize(
    "name,unit_price,quantity",
    [("banana",1.0,1),("banana",2.0,1)],
)
def test_cart_add_mismatched_price(name, unit_price, quantity):
    c = cart.Cart()
    c.add_item(name, unit_price, 1)
    if unit_price != 1.0:
        with pytest.raises(ValueError):
            c.add_item(name, unit_price, quantity)

# remove item

def test_cart_remove():
    c = cart.Cart()
    c.add_item("pear", 1.0, 4)
    c.remove_item("pear", 2)
    assert c.items() == [("pear", 1.0, 2)]
    c.remove_item("pear", 2)
    assert c.items() == []
    with pytest.raises(KeyError):
        c.remove_item("pear", 1)

# subtotal calculation

def test_cart_subtotal():
    c = cart.Cart()
    c.add_item("cherry", 10, 5)
    assert c.subtotal() == 50.0

# total with member flag and coupon

def test_cart_total_member_and_coupon():
    c = cart.Cart()
    # 20 items of bread at $2 -> subtotal 40
    c.add_item("bread", 2, 10)
    # bulk discount: qty 10 => 5% on each item
    # apply_discount should be applied to unit price before total? Spec ambiguous; we test against expected calculation
    bread_unit = cart.apply_discount(2, cart.bulk_discount_percent(10))
    subtotal = bread_unit * 10
    c.add_item("milk", 3, 4)  # no bulk discount
    subtotal += 3 * 4
    # shipping fee: subtotal <1000, non-member => 60
    assert c.total() == round(subtotal + 60, 2)
    # member true => 30
    assert c.total(member=True) == round(subtotal + 30, 2)
    # coupon SAVE10 applies 10% discount on subtotal before shipping
    assert c.total(coupon="SAVE10") == round(subtotal * 0.9 + 60, 2)
