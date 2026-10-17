import pytest
import cart

# Helper functions for expected calculations per specification

def apply_discount_expected(price: float, percent: float) -> float:
    """Return price reduced by percent percent, rounded to 2 decimals."""
    return round(price * (100 - percent) / 100, 2)


def bulk_discount_percent_expected(quantity: int) -> int:
    """Return bulk discount percent according to the specification.

    quantity >= 100  -> 15
    quantity >= 50   -> 10
    quantity >= 10   -> 5
    otherwise        -> 0
    """
    if quantity >= 100:
        return 15
    elif quantity >= 50:
        return 10
    elif quantity >= 10:
        return 5
    else:
        return 0


def shipping_fee_expected(subtotal: float, member: bool = False) -> float:
    """Return the shipping fee per specification.

    - If subtotal >= 1000 shipping is free (fee 0).
    - Otherwise the fee is 60; members pay half of it (30).
    """
    if subtotal >= 1000:
        return 0
    fee = 60
    if member:
        fee /= 2
    return fee


def parse_coupon_expected(code: str) -> int:
    """Parse coupon according to the specification.

    A valid code is "SAVE" followed by an integer N with 1 <= N <= 50,
    case‑insensitive, and whitespace ignored. Raises ValueError for any
    other input.
    """
    if not isinstance(code, str):
        raise ValueError("coupon must be a string")
    text = code.strip()
    if not text.lower().startswith("save"):
        raise ValueError(f"invalid coupon: {code!r}")
    digits = text[4:]
    if not digits.isdigit():
        raise ValueError(f"invalid coupon: {code!r}")
    percent = int(digits)
    if percent < 1 or percent > 50:
        raise ValueError(f"coupon percent out of range: {percent}")
    return percent


def compute_expected_subtotal(items):
    """Compute expected subtotal for a list of items.

    Items is an iterable of tuples (name, unit_price, quantity).
    """
    total = 0.0
    for _name, unit_price, qty in items:
        line_total = unit_price * qty
        discount_percent = bulk_discount_percent_expected(qty)
        discounted_line = round(line_total * (100 - discount_percent) / 100, 2)
        total += discounted_line
    return round(total, 2)


def compute_expected_total(items, coupon=None, member=False):
    """Compute expected total for given items, optional coupon and membership."""
    subtotal = compute_expected_subtotal(items)
    if coupon is not None:
        percent = parse_coupon_expected(coupon)
        subtotal = round(subtotal * (100 - percent) / 100, 2)
    fee = shipping_fee_expected(subtotal, member)
    return round(subtotal + fee, 2)

# ---------- Tests for standalone functions ----------

@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200.0, 15, 170.0),
        (100.0, 20, 80.0),
        (50.0, 0, 50.0),
        (99.99, 10, 90.0),
    ],
)
def test_apply_discount_valid(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# Negative price or percent out of bounds should raise ValueError
@pytest.mark.parametrize("price,percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

@pytest.mark.parametrize(
    "quantity,expected",
    [
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),  # Expect 10 per specification; implementation is buggy.
        (99, 10),
        (100, 15),
    ],
)
def test_bulk_discount_percent_boundary(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# Invalid quantity types or values raise ValueError
@pytest.mark.parametrize("quantity", [0, -5, 3.14])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        (" SAVE30 ", 30),
        ("sAvE5", 5),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVEx10",
    "SAVE0",
    "SAVE51",
    "save",  # case-insensitive but missing digits; should raise ValueError due to startswith failure.
    "",  # empty string
    None,
    123,
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (-10, False, ValueError),  # negative subtotal should raise ValueError
        (0, False, 60),
        (999.99, False, 60),
        (1000, False, 0),
        (1200, True, 30),
        (999.99, True, 30),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(ValueError):
            cart.shipping_fee(subtotal, member)
    else:
        assert cart.shipping_fee(subtotal, member) == expected

# ---------- Tests for Cart class ----------

def test_cart_add_item_and_items():
    c = cart.Cart()
    c.add_item("apple", 1.0, quantity=2)
    # Adding same item with same price should accumulate
    c.add_item("apple", 1.0, quantity=3)
    assert c.items() == {"apple": 5}

    # Adding a new item
    c.add_item("banana", 0.5)
    assert c.items() == {"apple": 5, "banana": 1}

    # Mismatched price raises ValueError
    with pytest.raises(ValueError):
        c.add_item("apple", 2.0)

    # Negative unit_price raises ValueError
    with pytest.raises(ValueError):
        c.add_item("orange", -1.0)

    # Zero unit_price is allowed
    c.add_item("watermelon", 0.0, quantity=4)
    assert c.items()["watermelon"] == 4

    # Quantity must be positive integer
    with pytest.raises(ValueError):
        c.add_item("kiwi", 1.5, quantity=0)
    with pytest.raises(ValueError):
        c.add_item("kiwi", 1.5, quantity=-2)
    with pytest.raises(ValueError):
        c.add_item("kiwi", 1.5, quantity=1.5)  # float quantity


def test_cart_remove_item_and_items():
    c = cart.Cart()
    c.add_item("apple", 1.0, quantity=5)
    c.remove_item("apple", quantity=3)
    assert c.items() == {"apple": 2}

    # Removing remaining quantity should delete the item per specification
    c.remove_item("apple", quantity=2)
    assert "apple" not in c.items()

    # Removing more than existing quantity deletes the item
    c.add_item("banana", 0.5, quantity=1)
    c.remove_item("banana", quantity=3)
    assert "banana" not in c.items()

    # Removing non‑existent item raises KeyError
    with pytest.raises(KeyError):
        c.remove_item("cherry")


def test_cart_subtotal_empty_and_no_discount():
    c = cart.Cart()
    assert c.subtotal() == 0.0

    c.add_item("apple", 10.0, quantity=2)  # No bulk discount (<10)
    assert c.subtotal() == 20.0


def test_cart_subtotal_with_bulk_discount():
    c = cart.Cart()
    # Quantity exactly at boundary for each tier
    c.add_item("item10", 5.0, quantity=10)   # percent 5
    c.add_item("item50", 2.0, quantity=50)   # percent 10 (spec)
    c.add_item("item100", 1.0, quantity=100) # percent 15
    expected = compute_expected_subtotal([
        ("item10", 5.0, 10),
        ("item50", 2.0, 50),
        ("item100", 1.0, 100),
    ])
    assert c.subtotal() == expected


def test_cart_total_empty_and_basic():
    c = cart.Cart()
    assert c.total() == 0.0

    # No coupon, non‑member
    c.add_item("apple", 10.0, quantity=5)
    assert c.total(member=False) == compute_expected_total([
        ("apple", 10.0, 5),
    ], member=False)

    # Non‑member with a valid coupon
    assert c.total(coupon="SAVE20") == compute_expected_total([
        ("apple", 10.0, 5),
    ], coupon="SAVE20")

    # Member flag changes shipping fee
    assert c.total(member=True) == compute_expected_total([
        ("apple", 10.0, 5),
    ], member=True)
    assert c.total(coupon="SAVE20", member=True) == compute_expected_total([
        ("apple", 10.0, 5),
    ], coupon="SAVE20", member=True)

    # Invalid coupon raises ValueError
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")


def test_cart_total_cross_threshold_bug():
    """Test scenario where subtotal > 1000 but coupon brings it below threshold.

    The specification requires shipping to be calculated on the discounted amount,
    so a correct total would include a $60 fee for a non‑member. The current
    implementation incorrectly calculates shipping based on the original
    (pre‑discount) subtotal, which results in free shipping when the
    pre‑discount subtotal exceeds $1000.
    """
    c = cart.Cart()
    # One item that makes subtotal 1200 before discount (e.g., 200*6)
    c.add_item("expensive", 200.0, quantity=6)  # 1200 subtotal
    expected_total = compute_expected_total([
        ("expensive", 200.0, 6),
    ], coupon="SAVE30")  # 30% off brings discounted amount to 840 (<1000)
    assert c.total(coupon="SAVE30") == expected_total

# ---------- End of tests ----------
