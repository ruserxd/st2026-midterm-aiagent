import pytest
import cart

# ---------- apply_discount tests ----------
@pytest.mark.parametrize(
    "price,percent,result",
    [
        (200, 15, 170.0),   # example from spec
        (100, 0, 100.0),    # no discount
        (50, 100, 0.0),     # full discount
        (123.456, 10, 111.11),  # rounding to two decimals
    ],
)
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize(
    "price,percent",
    [(-1, 10), (10, -5), (10, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent tests ----------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),   # expected according to spec
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon tests ----------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save5", 5),
        ("  SaVe50  ", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "DISCOUNT10", "SAVEX5", "save-5", "", "123"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee tests ----------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (500, True, 30),
        (999.99, False, 60),
        (1000, False, 0),
        (2000, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class tests ----------
def test_cart_basic_operations():
    c = cart.Cart()
    assert c.items() == {}
    c.add_item("apple", 2.0, quantity=3)
    c.add_item("banana", 1.5, quantity=4)
    assert c.items() == {"apple": 3, "banana": 4}
    # Verify that adding the same item increases quantity
    c.add_item("apple", 2.0, quantity=2)
    assert c.items()["apple"] == 5

def test_cart_add_invalid_parameters():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("negative_price", -1.0)      # negative unit price
    with pytest.raises(ValueError):
        c.add_item("zero_qty", 5.0, quantity=0)   # non‑positive quantity
    with pytest.raises(ValueError):
        c.add_item("float_qty", 2.5, quantity=3.5)  # non‑integer quantity

def test_cart_subtotal():
    c = cart.Cart()
    c.add_item("itemA", 10.0, quantity=5)   # no bulk discount
    c.add_item("itemB", 4.0, quantity=15)   # qty>=10 -> 5% discount
    line_a = 10 * 5                # 50.0
    line_b = 4 * 15                # 60.0
    expected_subtotal = round(line_a + cart.apply_discount(line_b, cart.bulk_discount_percent(15)), 2)
    assert c.subtotal() == pytest.approx(expected_subtotal)

def test_cart_remove_item():
    c = cart.Cart()
    c.add_item("orange", 3.0, quantity=5)
    # Remove part of the quantity
    c.remove_item("orange", quantity=2)
    assert c.items()["orange"] == 3
    # Removing all should delete the item entirely
    c.remove_item("orange", quantity=3)
    assert "orange" not in c.items()
    # Attempting to remove a non‑existent item raises KeyError
    with pytest.raises(KeyError):
        c.remove_item("pear")
    # Removing more than existing quantity should simply delete the item
    c.add_item("pear", 4.0, quantity=2)
    c.remove_item("pear", quantity=5)  # no exception expected
    assert "pear" not in c.items()

def test_cart_total_no_coupon_and_shipping():
    # Subtotal >=1000 -> free shipping
    c = cart.Cart()
    c.add_item("expensive", 200.0, quantity=6)   # subtotal 1200
    assert c.total() == pytest.approx(1200)
    # Subtotal <1000 but >0 -> shipping fee applies
    c2 = cart.Cart()
    c2.add_item("midprice", 300.0, quantity=3)  # subtotal 900
    expected_total_nonmember = round(900 + cart.shipping_fee(900, False), 2)
    assert c2.total() == pytest.approx(expected_total_nonmember)
    expected_member_total = round(900 + cart.shipping_fee(900, True), 2)
    assert c2.total(member=True) == pytest.approx(expected_member_total)

def test_cart_total_with_coupon_and_correct_shipping():
    # Setup a subtotal that crosses the free shipping threshold
    c = cart.Cart()
    c.add_item("widget", 100.0, quantity=10)   # 1000 -> bulk discount applies
    c.add_item("gizmo", 20.0, quantity=5)     # subtotal before coupon ~1050
    base_subtotal = c.subtotal()
    assert base_subtotal == pytest.approx(1050)
    # Apply a valid coupon (e.g., SAVE20 -> 20% off)
    discounted_amount = cart.apply_discount(base_subtotal, 20)
    shipping_nonmember = cart.shipping_fee(discounted_amount, False)
    shipping_member = cart.shipping_fee(discounted_amount, True)

    expected_total_nonmember = round(discounted_amount + shipping_nonmember, 2)
    expected_total_member = round(discounted_amount + shipping_member, 2)

    assert c.total(coupon="SAVE20") == pytest.approx(expected_total_nonmember)
    assert c.total(member=True, coupon="SAVE20") == pytest.approx(expected_total_member)

def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0
