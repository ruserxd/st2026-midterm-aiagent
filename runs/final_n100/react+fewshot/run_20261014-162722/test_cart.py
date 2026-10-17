import pytest
import cart

# Helper function to create a simple cart with a single item for testing

def make_cart(name="item", unit_price=100, quantity=1):
    c = cart.Cart()
    c.add_item(name, unit_price, quantity)
    return c

# ------------------ apply_discount ------------------
@pytest.mark.parametrize("price, percent, expected", [
    (200, 15, 170.0),   # example from spec
    (100, 0, 100.0),    # no discount
    (50, 100, 0.0),     # full discount
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# invalid price or percent
@pytest.mark.parametrize("price, percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ------------------ bulk_discount_percent ------------------
@pytest.mark.parametrize("qty, expected", [
    (9, 0),   # less than 10
    (10, 5),  # boundary 10
    (49, 5),  # just below 50
    (50, 10), # boundary 50
    (99, 10), # just below 100
    (100, 15),# boundary 100
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

# invalid quantity
@pytest.mark.parametrize("qty", [0, -5, 3.2])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(int(qty))

# ------------------ parse_coupon ------------------
@pytest.mark.parametrize("code, expected", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# invalid coupons
@pytest.mark.parametrize("code", ["SAV5", "SAVE0", "SAVE51", "DISCOUNT10", ""] )
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ------------------ shipping_fee ------------------
@pytest.mark.parametrize("subtotal, member, expected", [
    (0, False, 60),
    (500, True, 30),
    (1000, False, 0),
    (1500, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# invalid subtotal
@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ------------------ Cart methods ------------------
# add_item and items retrieval

def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item("apple", 2.5, 3)
    assert c.items() == {"apple": (2.5, 3)}
    # adding same item increases quantity
    c.add_item("apple", 2.5, 2)
    assert c.items() == {"apple": (2.5, 5)}

# add_item with mismatched price raises ValueError

def test_cart_add_mismatched_price():
    c = cart.Cart()
    c.add_item("banana", 1.0)
    with pytest.raises(ValueError):
        c.add_item("banana", 1.5)

# remove_item reduces quantity and removes when zero

def test_cart_remove_item():
    c = cart.Cart()
    c.add_item("orange", 3.0, 4)
    c.remove_item("orange", 2)
    assert c.items() == {"orange": (3.0, 2)}
    c.remove_item("orange", 2)  # should remove entirely
    assert c.items() == {}

# removing non-existent item raises KeyError

def test_cart_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("pear")

# subtotal calculation

def test_cart_subtotal():
    c = cart.Cart()
    c.add_item("pen", 1.2, 5)
    c.add_item("notebook", 3.5, 2)
    assert c.subtotal() == pytest.approx(1.2*5 + 3.5*2)

# total with member and coupon

def test_cart_total_member_and_coupon():
    c = cart.Cart()
    c.add_item("tshirt", 20, 4)   # subtotal 80
    # no discount
    assert c.total(member=False) == pytest.approx(80 + 60)
    # member reduces shipping by half
    assert c.total(member=True) == pytest.approx(80 + 30)
    # apply coupon 10%
    c.add_item("hat", 15, 1)      # subtotal now 95
    assert c.total(coupon="SAVE10") == pytest.approx(95*0.90 + 60)
    # member with coupon
    assert c.total(member=True, coupon="SAVE20") == pytest.approx(95*0.80 + 30)
