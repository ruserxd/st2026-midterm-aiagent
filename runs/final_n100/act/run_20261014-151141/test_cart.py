import pytest
import cart

# ---------- apply_discount ----------

@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200, 15, 170.0),
        (100, 0, 100.0),
        (50, 100, 0.0),
        (123.45, 10, 111.11),  # 123.45 * 0.9 = 111.105 -> round to 2 decimals
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == pytest.approx(expected, rel=1e-12)

@pytest.mark.parametrize("price,percent", [( -5, 10), (100, -1), (100, 101)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------

@pytest.mark.parametrize(
    "quantity,expected",
    [
        (5, 0),
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

@pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------

@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        (" SAVE30 ", 30),
        ("sAvE50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVE0",
    "SAVE51",
    "DISCOUNT10",
    "SAVExx",
    "  ",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------

@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (0, False, 60),
        (500, True, 30),
        (1000, False, 0),
        (1200, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class basics ----------

def test_cart_add_and_items():
    c = cart.Cart()
    assert c.items() == {}
    c.add_item("apple", 1.0, quantity=3)
    assert c.items() == {"apple": 3}
    c.add_item("banana", 0.5)
    assert c.items() == {"apple": 3, "banana": 1}


def test_cart_remove():
    c = cart.Cart()
    c.add_item("orange", 2.0, quantity=5)
    c.remove_item("orange", quantity=2)
    assert c.items() == {"orange": 3}
    c.remove_item("orange", quantity=3)  # should remove the item entirely
    assert c.items() == {}


def test_cart_subtotal_and_total():
    c = cart.Cart()
    c.add_item("book", 30.0, quantity=2)
    c.add_item("pen", 5.0, quantity=4)
    assert c.subtotal() == pytest.approx(70.0)

    # No discounts
    assert c.total() == pytest.approx(70.0 + 60)  # shipping fee 60

    # Member discount via bulk and coupon
    c.add_item("book", 30.0, quantity=10)  # total books now 12, bulk discount 5%
    total_no_coupon = c.total(member=True)
    # subtotal after bulk discount on books only
    book_subtotal = (30.0 * 12) * 0.95  # bulk discount
    other_subtotal = 5.0 * 4
    expected_subtotal = book_subtotal + other_subtotal
    shipping = cart.shipping_fee(expected_subtotal, member=True)
    assert total_no_coupon == pytest.approx(expected_subtotal + shipping)

    # With coupon SAVE10 (10%) on entire subtotal
    total_with_coupon = c.total(member=True, coupon="SAVE10")
    discounted_total = expected_subtotal * 0.9
    shipping_fee = cart.shipping_fee(discounted_total, member=True)
    assert total_with_coupon == pytest.approx(discounted_total + shipping_fee)
