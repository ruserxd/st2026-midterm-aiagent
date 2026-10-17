import pytest
import cart

# Helper function that implements the bulk discount rules according to the specification.
def correct_bulk_discount(quantity):
    if quantity >= 100:
        return 15
    elif quantity >= 50:
        return 10
    elif quantity >= 10:
        return 5
    else:
        return 0

# ---------------------------------------------------------------------------
# Tests for apply_discount
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 50, 25.0),
    (12.34, 33, round(12.34 * (100 - 33) / 100, 2)),
])
def test_apply_discount_valid_cases(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [
    (-1, 10),
    (100, -5),
    (100, 101),
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------------------------------------------------------------------------
# Tests for bulk_discount_percent
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("quantity,expected", [
    (5, 0),
    (10, 5),
    (49, 5),
    (50, 10),   # expected according to spec – will fail due to implementation bug
    (51, 10),
    (100, 15),
    (101, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, "5"])
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------------------------------------------------------------------------
# Tests for parse_coupon
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("  SaVe20   ", 20),
    ("save30", 30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["", "SAVE", "SAve", "SAVEBAD", "SAVE0", "SAVE51", None, 123])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------------------------------------------------------------------------
# Tests for shipping_fee and its constants
# ---------------------------------------------------------------------------
def test_shipping_fee_constants():
    assert getattr(cart, "FREE_SHIPPING_THRESHOLD", None) == 1000
    assert getattr(cart, "SHIPPING_BASE", None) == 60

@pytest.mark.parametrize("subtotal,expected", [
    (0, 60),
    (999.99, 60),
    (1000, 0),
])
def test_shipping_fee_non_member(subtotal, expected):
    assert cart.shipping_fee(subtotal) == expected

@pytest.mark.parametrize("subtotal,expected", [
    (500, 30.0),
])
def test_shipping_fee_member(subtotal, expected):
    assert cart.shipping_fee(subtotal, member=True) == expected

def test_shipping_fee_negative_subtotal_raises():
    with pytest.raises(ValueError):
        cart.shipping_fee(-1)

# ---------------------------------------------------------------------------
# Tests for Cart.add_item and related behavior
# ---------------------------------------------------------------------------
def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item("Apple", 5, 3)
    assert c.items() == {"Apple": 3}
    # add same item with same price increases quantity
    c.add_item("Apple", 5, 2)
    assert c.items() == {"Apple": 5}
    # adding same name with different price raises ValueError
    with pytest.raises(ValueError):
        c.add_item("Apple", 6, 1)
    # negative unit price or non‑positive quantity raise ValueError
    with pytest.raises(ValueError):
        c.add_item("Banana", -1, 1)
    with pytest.raises(ValueError):
        c.add_item("Banana", 1, 0)

def test_cart_items_copy():
    c = cart.Cart()
    c.add_item("Orange", 2, 4)
    items_dict = c.items()
    items_dict["Orange"] = 100
    # internal state should not be affected
    assert c.items() == {"Orange": 4}

# ---------------------------------------------------------------------------
# Tests for Cart.remove_item
# ---------------------------------------------------------------------------
def test_cart_remove_item():
    c = cart.Cart()
    c.add_item("Apple", 5, 5)
    # remove part of quantity
    c.remove_item("Apple", 2)
    assert c.items() == {"Apple": 3}
    # removing the remaining quantity should remove the item entirely – spec
    c.remove_item("Apple", 3)
    assert "Apple" not in c.items()
    # removing an absent item raises KeyError.
    with pytest.raises(KeyError):
        c.remove_item("Banana")
    # removing more than present deletes the item
    c.add_item("Pear", 3, 2)
    c.remove_item("Pear", 5)  # quantity goes negative – should delete
    assert "Pear" not in c.items()

# ---------------------------------------------------------------------------
# Tests for Cart.subtotal
# ---------------------------------------------------------------------------
def test_cart_subtotal_empty_and_cases():
    c = cart.Cart()
    assert c.subtotal() == 0

    # quantity <10 – no discount
    c.add_item("Widget", 12.34, 3)
    expected = round(12.34 * 3 * (100 - correct_bulk_discount(3)) / 100, 2)
    assert c.subtotal() == expected

# ---------------------------------------------------------------------------
# Tests for Cart.subtotal rounding issue
# ---------------------------------------------------------------------------
def test_cart_subtotal_rounding_issue():
    c = cart.Cart()
    c.add_item("Item1", 33.333, 12)  # quantity >=10 => 5% discount
    c.add_item("Item2", 66.666, 6)   # no discount
    # Compute expected subtotal per spec (round only after summing)
    percent1 = correct_bulk_discount(12)  # 5%
    line_total1 = 33.333 * 12
    discounted1 = line_total1 * (100 - percent1) / 100
    percent2 = correct_bulk_discount(6)   # 0%
    line_total2 = 66.666 * 6
    discounted2 = line_total2 * (100 - percent2) / 100
    expected_subtotal = round(discounted1 + discounted2, 2)
    assert c.subtotal() == expected_subtotal

# ---------------------------------------------------------------------------
# Tests for Cart.total
# ---------------------------------------------------------------------------
def test_cart_total_no_coupon():
    c = cart.Cart()
    c.add_item("TestItem", 20, 1)
    # subtotal=20 - shipping 60 - total 80
    assert c.total() == 80.0

def test_cart_total_member():
    c = cart.Cart()
    c.add_item("TestItem", 20, 1)
    # subtotal=20 - member half fee (30) - total 50
    assert c.total(member=True) == 50.0

def test_cart_total_with_coupon_discount_below_threshold():
    c = cart.Cart()
    c.add_item("Expensive", 1200, 1)
    # subtotal=1200; coupon 20% -> amount=960 (<1000); shipping fee 60 = total expected 1020
    assert c.total(coupon="SAVE20") == 1020.0

def test_cart_total_with_coupon_and_member():
    c = cart.Cart()
    c.add_item("Expensive", 1200, 1)
    # subtotal=1200; coupon 20% -> amount=960 (<1000); member half fee (30) = total expected 990
    assert c.total(member=True, coupon="SAVE20") == 990.0

def test_cart_total_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item("Item", 50, 1)
    with pytest.raises(ValueError):
        c.total(coupon="BAD")

def test_cart_total_empty_with_coupon():
    c = cart.Cart()
    assert c.total(coupon="SAVE10") == 0

# ---------------------------------------------------------------------------
# Debug test to inspect Cart subtotal internal state
# ---------------------------------------------------------------------------
def test_debug_cart_subtotal_lines():
    c = cart.Cart()
    c.add_item("Widget", 12.34, 3)
    print("cart._lines:", c._lines)
    try:
        subtotal_val = c.subtotal()
        print("subtotal returned:", subtotal_val)
    except Exception as e:
        import traceback, sys
        traceback.print_exc(file=sys.stdout)
        raise
