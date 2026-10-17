import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# ---------- Helper for floating comparison ----------

@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert apply_discount(price, percent) == expected

# invalid price or percent
@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- bulk_discount_percent ----------
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (1, 0),
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
    assert bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon ----------
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save5", 5),
        ("  SAVE20  ", 20),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["SAVEX", "SAVE0", "SAVE51", "DISCOUNT10", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ----------
@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (1000, False, 0),
        (1500, True, 0),
        (999.99, False, 60),
        (999.99, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_invalid_subtotal(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class ----------

def test_cart_basic_operations():
    cart = Cart()
    assert cart.items() == {}

    # add items
    cart.add_item("Apple", 0.5, 2)
    cart.add_item("Banana", 0.3)  # default quantity 1
    expected_items = {"Apple": (0.5, 2), "Banana": (0.3, 1)}
    assert cart.items() == expected_items

    # subtotal calculation
    assert cart.subtotal() == pytest.approx(0.5 * 2 + 0.3)

    # add more quantity to existing item
    cart.add_item("Apple", 0.5, 3)
    assert cart.items()["Apple"] == (0.5, 5)

    # remove items partially
    cart.remove_item("Apple", 2)
    assert cart.items()["Apple"] == (0.5, 3)

    # remove more than existing quantity -> item removed
    cart.remove_item("Banana")
    assert "Banana" not in cart.items()

    # total with no discount or coupon
    assert cart.total() == pytest.approx(cart.subtotal())

    # total as member with shipping fee free over 1000
    large_cart = Cart()
    large_cart.add_item("Expensive", 1200)
    assert large_cart.total(member=True) == pytest.approx(1200)

    # total with coupon and discount
    cart.add_item("Milk", 1.5, 10)  # triggers bulk discount of 5%
    coupon_percent = parse_coupon("SAVE20")
    # expected: subtotal includes bulk discounted Milk price (after 5%) then apply coupon percent to whole subtotal
    milk_discounted_price = apply_discount(1.5 * 10, 5)
    new_subtotal = cart.subtotal() - (1.5 * 10) + milk_discounted_price
    expected_total = apply_discount(new_subtotal, coupon_percent)
    assert cart.total(coupon="SAVE20") == pytest.approx(expected_total)
