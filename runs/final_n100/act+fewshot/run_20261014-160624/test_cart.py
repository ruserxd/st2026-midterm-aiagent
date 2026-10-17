import pytest
import cart

# ----- apply_discount tests -----
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount_basic(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# boundary price/percent checks
@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101, 200])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# rounding check
assert cart.apply_discount(99.999, 10) == round(99.999 * 0.9, 2)

# ----- bulk_discount_percent tests -----
@pytest.mark.parametrize("qty,expected", [
    (5, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0, -1, 3.5])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ----- parse_coupon tests -----
valid_codes = {
    "SAVE10": 10,
    "save25": 25,
    " SAVE5 ": 5,
    "SaVe50": 50,
}

@pytest.mark.parametrize("code,expected", list(valid_codes.items()))
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

invalid_codes = ["SAVE0", "SAVEXX", "10SAVE", "", " S V A E "]
@pytest.mark.parametrize("code", invalid_codes)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ----- shipping_fee tests -----
@pytest.mark.parametrize("subtotal,member,expected", [
    (999.99, False, 60),
    (1000, False, 0),
    (1500, True, 30),
    (50, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ----- Cart class tests -----
@pytest.fixture
def empty_cart():
    return cart.Cart()

@pytest.fixture
def filled_cart():
    c = cart.Cart()
    c.add_item("Widget", 20.0, quantity=5)  # subtotal 100
    c.add_item("Gadget", 10.0, quantity=3)  # subtotal 30, total 130
    return c

# items and subtotal

def test_cart_items_and_subtotal(empty_cart):
    assert empty_cart.items() == []
    assert empty_cart.subtotal() == 0


def test_add_item(filled_cart):
    assert len(filled_cart.items()) == 2
    # Check subtotal recomputed correctly
    assert filled_cart.subtotal() == 130.0


def test_remove_item(filled_cart):
    c = filled_cart
    c.remove_item("Widget", quantity=3)
    # Widget now 2 left at $20 = 40, Gadget still 30 = total 70
    assert c.subtotal() == 70.0
    # Removing more than existing should raise ValueError
    with pytest.raises(ValueError):
        c.remove_item("Widget", quantity=5)

# total calculations

def test_cart_total_no_coupon(filled_cart):
    # subtotal 130, no coupon, member False = shipping 60 -> 190
    assert filled_cart.total(member=False) == round(190.0, 2)


def test_cart_total_with_member(filled_cart):
    # shipping fee half: 30
    assert filled_cart.total(member=True) == round(160.0, 2)


def test_cart_total_with_coupon(filled_cart):
    # coupon SAVE10 reduces by 10% of subtotal 130 = 117, then shipping 60 -> 177
    assert filled_cart.total(coupon="SAVE10") == round(177.0, 2)


def test_cart_total_invalid_coupon(filled_cart):
    with pytest.raises(ValueError):
        filled_cart.total(coupon="BADCODE")

# empty cart total

def test_empty_cart_total(empty_cart):
    assert empty_cart.total() == 0.0
