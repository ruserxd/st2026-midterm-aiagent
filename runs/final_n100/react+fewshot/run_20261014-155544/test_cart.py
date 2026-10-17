import pytest
import cart

# ---------- apply_discount ---------------------------------

@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),          # example from spec
        (100, 0, 100.0),           # no discount
        (50, 100, 0.0),            # full discount
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize(
    "price, percent",
    [(-10, 20), (50, -5), (50, 105)],
)
def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ---------------------------------

@pytest.mark.parametrize(
    "quantity, expected",
    [
        (5, 0),   # below 10
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -1, 3.5],
)
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ---------------------------------

@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save5", 5),
        ("  SaVe50  ", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    ["", "SAVE0", "SAVEBAD", "12345", " SAVE51 ", "SAVE-5", "   "]
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ---------------------------------

@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (999, False, 60),
        (1000, False, 0),
        (1500, True, 30),
        (1200, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-10, -1],
)
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ---------------------------------

def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item("apple", 1.0, 3)
    c.add_item("banana", 0.5)
    assert c.items() == {"apple": 3, "banana": 1}

    # adding existing item with same price increases quantity
    c.add_item("apple", 1.0, 2)
    assert c.items()["apple"] == 5

    # mismatched unit_price raises ValueError
    with pytest.raises(ValueError):
        c.add_item("apple", 1.5, 1)

    # invalid unit price or quantity raise ValueError
    with pytest.raises(ValueError):
        c.add_item("orange", -0.2, 1)
    with pytest.raises(ValueError):
        c.add_item("orange", 0.2, 0)


def test_cart_remove_and_deletion():
    c = cart.Cart()
    c.add_item("apple", 1.0, 3)
    # remove less than quantity
    c.remove_item("apple", 1)
    assert c.items()["apple"] == 2
    # removing more should delete the item (spec says <=0 removed)
    c.remove_item("apple", 2)
    assert "apple" not in c.items()


def test_cart_subtotal_and_bulk_discount():
    c = cart.Cart()
    # quantity 10 -> 5% discount on line total
    c.add_item("item", 100.0, 10)  # line_total=1000, discount=50 => 950
    assert c.subtotal() == 950.00

    # quantity 99 -> 10% discount
    c = cart.Cart()
    c.add_item("item", 200.0, 99)
    line_total = 200 * 99
    discounted = line_total * (1 - 0.10)
    assert c.subtotal() == round(discounted, 2)


def test_cart_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("item", 500.0, 3)  # 1500 total, no bulk discount
    # subtotal should be 1500
    assert c.subtotal() == 1500.00

    # Apply coupon SAVE10 (10% off)
    amount_after_coupon = cart.apply_discount(1500, 10)
    # shipping on discounted amount: since discounted < 1000? 1350 -> fee 60
    expected_shipping = cart.shipping_fee(amount_after_coupon, member=False)
    total_expected = round(amount_after_coupon + expected_shipping, 2)
    assert c.total(coupon="SAVE10") == total_expected

    # Test member discount on shipping
    total_member = round(amount_after_coupon + cart.shipping_fee(amount_after_coupon, member=True), 2)
    assert c.total(member=True, coupon="SAVE10") == total_member


def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0
    # Even with shipping fee on empty should be 0 per spec
