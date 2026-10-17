import pytest
import cart

# Utility for creating a cart with common items
def make_cart():
    c = cart.Cart()
    c.add_item("apple", 100, 2)
    c.add_item("banana", 200, 1)
    return c

###########################
# apply_discount tests
###########################
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
        (123.456, 10, round(123.456 * 0.9, 2)),
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price, percent",
    [(-1, 10), (100, -5), (100, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

###########################
# bulk_discount_percent tests
###########################
@pytest.mark.parametrize(
    "quantity, expected",
    [
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

@pytest.mark.parametrize(
    "quantity",
    [0, -1, 3.5, 'ten'],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

###########################
# parse_coupon tests
###########################
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save5", 5),
        (" SAVE20 ", 20),
        ("SaVe50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    ["SAVE0", "SAVE51", "NOTVALID", "SAVEBAD", "", None],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

###########################
# shipping_fee tests
###########################
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (1000, False, 0),
        (1200, True, 0),
        (999.99, False, 60),
        (500, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-1, -100],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

###########################
# Cart class tests
###########################
def test_cart_initial_state():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 60  # member=False, no coupon, subtotal 0 => shipping 60

def test_add_and_remove_items():
    c = make_cart()
    expected_items = {
        "apple": (100, 2),
        "banana": (200, 1),
    }
    assert c.items() == expected_items
    # subtotal: 100*2 + 200*1 = 400
    assert c.subtotal() == 400
    # total without coupon/member
    assert c.total() == 460  # 400 + 60 shipping

    # Add more apples
    c.add_item("apple", 100, 3)
    assert c.items()["apple"] == (100, 5)
    assert c.subtotal() == 700
    assert c.total() == 760

    # Remove some bananas
    c.remove_item("banana")
    assert "banana" not in c.items()
    assert c.subtotal() == 500
    assert c.total() == 560

    # Removing more than present should raise ValueError
    with pytest.raises(ValueError):
        c.remove_item("apple", quantity=10)

def test_cart_with_member_and_coupon():
    c = make_cart()
    # subtotal 400, shipping 60 => total 460
    assert c.total(member=True) == 440  # member discount half shipping
    # apply coupon SAVE10 (10% off after shipping?) spec unclear: use discount on subtotal
    discounted_subtotal = cart.apply_discount(c.subtotal(), cart.parse_coupon("SAVE10"))
    total_with_coupon = discounted_subtotal + cart.shipping_fee(c.subtotal())
    assert c.total(coupon="SAVE10") == total_with_coupon

# Edge case: coupon that results in zero subtotal
    c.add_item("free", 0, 5)
    assert c.total(coupon="SAVE50") == 60  # shipping still applies because subtotal 0
