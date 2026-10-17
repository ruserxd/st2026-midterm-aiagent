import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# -------------------
# Helper functions
# -------------------

def almost_equal(a, b, eps=1e-9):
    return abs(a - b) < eps

# ---------------------------------
# Tests for apply_discount
# ---------------------------------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0
    # No discount
    assert apply_discount(100, 0) == 100.0
    # Full discount
    assert apply_discount(50, 100) == 0.0

@ pytest.mark.parametrize("price", [-1, -0.01])
@ pytest.mark.parametrize("percent", [10, 20])
def test_apply_discount_negative_price(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

@ pytest.mark.parametrize("price", [10, 20])
@ pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------------------------------
# Tests for bulk_discount_percent
# ---------------------------------

def test_bulk_discount_thresholds():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

def test_bulk_discount_invalid_quantity():
    for q in [0, -1, 3.5, "10"]:
        with pytest.raises(ValueError):
            bulk_discount_percent(q)

# ---------------------------------
# Tests for parse_coupon
# ---------------------------------

def test_parse_coupon_valid_cases():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20") == 20
    assert parse_coupon(" SAVE30 ") == 30

@ pytest.mark.parametrize(
    "code",
    ["SAVEX", "SA V E5", "1234", "save0", "save51", "", None],
)
def test_parse_coupon_invalid_cases(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------------------------------
# Tests for shipping_fee
# ---------------------------------

def test_shipping_fee_non_member():
    assert shipping_fee(0) == 60
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(2000) == 0

@ pytest.mark.parametrize("subtotal", [0, 500, 1000])
@ pytest.mark.parametrize("member", [True, False])
def test_shipping_fee_member(subtotal, member):
    expected = 30 if (not member and subtotal < 1000) else 0
    # For members below threshold, half the fee
    if member:
        if subtotal < 1000:
            assert shipping_fee(subtotal, True) == 30
        else:
            assert shipping_fee(subtotal, True) == 0
    else:
        if subtotal < 1000:
            assert shipping_fee(subtotal, False) == 60
        else:
            assert shipping_fee(subtotal, False) == 0

# ---------------------------------
# Tests for Cart class
# ---------------------------------

def test_cart_initial_empty():
    cart = Cart()
    assert cart.items() == {}
    assert cart.subtotal() == 0
    assert cart.total() == 0


def test_add_and_remove_items_basic():
    c = Cart()
    c.add_item("apple", 2.5, 4)
    c.add_item("banana", 1.0, 10)
    # Adding same item with same price increases quantity
    c.add_item("apple", 2.5, 6)
    assert c.items() == {"apple": 10, "banana": 10}
    # Removing reduces quantity
    c.remove_item("banana", 3)
    assert c.items()["banana"] == 7
    # Removing more than existing removes the item entirely
    c.remove_item("banana", 7)
    assert "banana" not in c.items()


def test_add_same_name_different_price():
    c = Cart()
    c.add_item("widget", 5.0, 1)
    with pytest.raises(ValueError):
        c.add_item("widget", 6.0, 2)


def test_subtotal_with_bulk_discount_and_rounding():
    # Create items to hit each discount tier
    c = Cart()
    # 9 units: no discount
    c.add_item("item1", 10.0, 9)   # line total 90
    # 10 units: 5% off
    c.add_item("item2", 20.0, 10)  # line total 200 -> after 5% = 190
    # 50 units: 10% off
    c.add_item("item3", 5.0, 50)   # line total 250 -> after 10% = 225
    # 100 units: 15% off
    c.add_item("item4", 1.0, 100)  # line total 100 -> after 15% = 85

    expected = round(90 + 190 + 225 + 85, 2)
    assert c.subtotal() == expected


def test_total_without_coupon_and_non_member():
    c = Cart()
    c.add_item("item", 10.0, 5)   # no bulk discount
    subtotal = c.subtotal()
    # shipping fee for subtotal <1000 => 60
    expected_total = round(subtotal + 60, 2)
    assert c.total() == expected_total


def test_total_with_coupon_and_member():
    c = Cart()
    c.add_item("item", 20.0, 10)   # bulk discount 5%
    subtotal_before_discount = c.subtotal()
    # Apply coupon SAVE10 => reduce by 10%
    after_coupon = apply_discount(subtotal_before_discount, parse_coupon("SAVE10"))
    # shipping fee computed on amount after coupon
    expected_shipping = 60 if after_coupon < 1000 else 0
    # member halves shipping
    expected_total = round(after_coupon + expected_shipping / 2, 2)
    assert c.total(member=True, coupon="SAVE10") == expected_total

# ---------------------------------
# Tests for spec compliance (edge cases)
# ---------------------------------

def test_invalid_coupon_in_cart_total():
    c = Cart()
    c.add_item("item", 5.0, 1)
    with pytest.raises(ValueError):
        c.total(coupon="invalid")

# ---------------------------------
# Run tests to ensure they fail or pass as expected
# ---------------------------------

if __name__ == "__main__":
    import sys
    from subprocess import run, PIPE
    result = run(["pytest", "-q", "test_cart.py"], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        sys.exit(1)
