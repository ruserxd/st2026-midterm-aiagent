import pytest
import cart

# ----- apply_discount -----
def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0


def test_apply_discount_rounding():
    # 10.55 * (100-25)/100 = 7.9125 rounded to 2 decimals is 7.91
    assert cart.apply_discount(10.55, 25) == 7.91

@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 20)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ----- bulk_discount_percent -----
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (1,0),(9,0),
        (10,5),(49,5),
        (50,10),(99,10),
        (100,15),(200,15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 3.5, "ten"])
def test_bulk_discount_invalid_input(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ----- parse_coupon -----
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        (" save20 ", 20),
        ("SaVe30", 30),
        ("sAVe40", 40),  # case-insensitive
        ("save50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        None,
        12345,
        "",
        "SAVE0",
        "SAVE51",
        "SAVEX10",
        "X_SAVE10",
        "SAVE-5",
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ----- shipping_fee -----
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (1000, False, 0),
        (999.99, False, 60),
        (500, True, 30),
        (1500, False, 0),
        (1200, True, 0),  # free shipping for members as well
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative_subtotal(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ----- Cart class -----
def test_cart_initial_state():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

def test_add_item_and_subtotal():
    c = cart.Cart()
    c.add_item("apple", 10, quantity=2)
    assert c.items() == {"apple": 2}
    assert c.subtotal() == 20.0

def test_bulk_discount_in_cart_subtotal():
    c = cart.Cart()
    c.add_item("book", 20, quantity=10)  # bulk discount 5%
    expected = round(20 * 10 * (100 - 5)/100, 2)
    assert c.subtotal() == expected

def test_add_same_item_increments():
    c = cart.Cart()
    c.add_item("pen", 5, quantity=1)
    c.add_item("pen", 5, quantity=3)
    assert c.items() == {"pen": 4}
    assert c.subtotal() == 20.0

def test_add_same_item_with_different_price_raises():
    c = cart.Cart()
    c.add_item("pen", 5, quantity=1)
    with pytest.raises(ValueError):
        c.add_item("pen", 6, quantity=1)

def test_remove_item_partial_and_full():
    c = cart.Cart()
    c.add_item("notebook", 15, quantity=3)
    c.remove_item("notebook", quantity=1)
    assert c.items() == {"notebook": 2}
    c.remove_item("notebook", quantity=2)  # should remove item entirely
    assert "notebook" not in c.items()

def test_remove_nonexistent_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("does_not_exist")

def test_total_without_coupon_and_member_status():
    c = cart.Cart()
    c.add_item("widget", 200, quantity=1)
    assert c.total(member=False) == 260.0
    assert c.total(member=True) == 230.0

def test_total_with_coupon_affecting_shipping_fee():
    c = cart.Cart()
    c.add_item("expensive", 1200, quantity=1)  # subtotal > 1000
    # Coupon reduces amount below free shipping threshold
    assert c.total(coupon="SAVE20") == 1020.0
    assert c.total(member=True, coupon="SAVE20") == 990.0

def test_total_with_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item("test", 10)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# ----- add_item error cases -----
def test_add_item_invalid_unit_price():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("bad", -5, quantity=1)

@pytest.mark.parametrize("quantity", [0, -3, 2.5, "five"])
def test_add_item_invalid_quantity(quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("bad", 10, quantity=quantity)
