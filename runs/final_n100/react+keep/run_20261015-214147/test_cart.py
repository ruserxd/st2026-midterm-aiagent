import pytest
import cart

# ------------------------------
# parse_coupon tests (spec based)
# ------------------------------

def test_parse_coupon_valid_cases():
    # valid codes with various whitespace and case
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon("  SaVe30   ") == 30

@pytest.mark.parametrize(
    "invalid_code",
    [
        "",  # empty string
        "SAVE0",  # below valid range
        "SAVE51",  # above valid range
        "DISCOUNT10",  # wrong prefix
        "SAVE-5",  # negative number
        "SAVE50x",  # extra characters
    ],
)
def test_parse_coupon_invalid_cases(invalid_code):
    with pytest.raises(ValueError):
        cart.parse_coupon(invalid_code)

# ------------------------------
# Cart.total tests (spec based)
# ------------------------------

def _create_cart_with_item(price=10.0, quantity=2):
    c = cart.Cart()
    c.add_item("Widget", unit_price=price, quantity=quantity)
    return c


def test_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0


def test_total_without_coupon_and_member_fee():
    # Use a known subtotal to compute expected shipping
    c = _create_cart_with_item(price=15.0, quantity=3)  # subtotal 45
    subtotal = c.subtotal()
    shipping = cart.shipping_fee(subtotal)
    expected = round(subtotal + shipping, 2)
    assert c.total() == expected


def test_total_with_valid_coupon_reduces_subtotal_and_adds_shipping():
    # subtotal before discount
    c = _create_cart_with_item(price=20.0, quantity=5)  # 100
    discount_percent = cart.parse_coupon("SAVE25")  # 25%
    discounted_amount = c.subtotal() * (1 - discount_percent / 100)
    shipping_after_discount = cart.shipping_fee(discounted_amount)
    expected = round(discounted_amount + shipping_after_discount, 2)
    assert c.total(coupon="SAVE25") == expected


def test_total_with_invalid_coupon_raises():
    c = _create_cart_with_item()
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
