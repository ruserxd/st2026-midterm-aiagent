import pytest
import cart

# ---------- Utility for expected values from the specifications ----------

# apply_discount should reduce price by percent% and round to 2 decimals.
# We test typical cases and boundary conditions.

@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (200.0, 15, 170.00),
        (100.0, 0, 100.00),
        (100.0, 100, 0.00),
        # rounding test
        (99.995, 10, 90.00),   # 99.995 * 0.9 = 89.9955 => round to 90.00
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# Percent boundaries and error handling.
@pytest.mark.parametrize(
    "price,percent",
    [(-10.0, 10), (100.0, -5), (100.0, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent discount tiers.
@pytest.mark.parametrize(
    "quantity,expected",
    [
        (9, 0),     # below 10
        (10, 5),    # threshold
        (49, 5),    # just below next tier
        (50, 10),   # threshold for 10%
        (99, 10),   # just below next tier
        (100, 15),  # threshold for 15%
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# bulk_discount_percent error when quantity not positive int.
@pytest.mark.parametrize(
    "quantity",
    [0, -1, 3.5, "10"],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon parses 'SAVE' followed by integer in range 1..50.
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SAVE10", 10),
        ("save5", 5),            # case-insensitive
        (" SAVE20 ", 20),         # surrounding whitespace ignored
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

# parse_coupon should raise for invalid codes.
@pytest.mark.parametrize(
    "code",
    [
        None,
        123,
        "",          # empty string
        "svae10",   # typo
        "SAVE0",     # percent out of range (<1)
        "SAVE51",   # percent out of range (>50)
        "DISCOUNT10",  # wrong prefix
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests: free above threshold, full fee otherwise, half for members.
FREE_THRESHOLD = 1000
BASE_FEE = 60
HALF_FEE = BASE_FEE / 2

@pytest.mark.parametrize(
    "subtotal,member,expected",
    [
        (1200.0, False, 0),           # free shipping
        (1000.0, True, 0),            # boundary condition: >= threshold is free
        (999.99, False, BASE_FEE),    # just below threshold
        (50.5, True, HALF_FEE),       # member gets half
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

# shipping_fee error on negative subtotal.
@pytest.mark.parametrize(
    "subtotal",
    [-1.0, -100],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart functionality tests: adding/removing items, subtotals and totals.

def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item("Apple", 0.50, quantity=3)   # subtotal 1.5 with no bulk discount
    assert c.items() == {"Apple": 3}

    # Adding same item increases quantity, but unit price must match.
    c.add_item("Apple", 0.50, quantity=2)
    assert c.items() == {"Apple": 5}

    with pytest.raises(ValueError):
        c.add_item("Apple", 0.60, quantity=1)   # different unit price

    # Negative or non-integer quantities raise ValueError.
    with pytest.raises(ValueError):
        c.add_item("Banana", 0.30, quantity=-2)
    with pytest.raises(ValueError):
        c.add_item("Banana", 0.30, quantity=1.5)

# Cart.remove_item reduces quantity and removes when zero or less.

def test_cart_remove():
    c = cart.Cart()
    c.add_item("Apple", 1.00, quantity=3)
    c.remove_item("Apple")  # default quantity 1
    assert c.items() == {"Apple": 2}
    c.remove_item("Apple", quantity=2)  # should remove item entirely
    assert c.items() == {}

    with pytest.raises(KeyError):
        c.remove_item("Nonexistent")

# Subtotal calculation with bulk discounts.

def test_cart_subtotal_no_discount():
    c = cart.Cart()
    c.add_item("Widget", 10.0, quantity=5)   # below bulk threshold, no discount
    assert c.subtotal() == 50.00


def test_cart_subtotal_with_bulk_discount():
    c = cart.Cart()
    c.add_item("Gadget", 20.0, quantity=12)   # bulk >=10 gives 5% discount
    expected_line_total = 20.0 * 12
    expected_discounts = cart.apply_discount(expected_line_total, 5)
    assert c.subtotal() == round(expected_discounts, 2)

# Total calculation: coupon and shipping.

def test_cart_total_no_coupon_or_member():
    c = cart.Cart()
    c.add_item("Book", 15.0, quantity=3)   # subtotal 45, no bulk discount
    expected = 45 + cart.shipping_fee(45)
    assert c.total() == round(expected, 2)

# Coupon reduces amount before shipping.
def test_cart_total_with_coupon():
    c = cart.Cart()
    c.add_item("Notebook", 30.0, quantity=2)   # subtotal 60
    # coupon 20% applied to subtotal first: 48, then shipping on 48
    expected_amount = 60 - (60 * 0.20)
    shipping = cart.shipping_fee(expected_amount)
    total_expected = round(expected_amount + shipping, 2)
    assert c.total(coupon="SAVE20") == total_expected

# Member status halves shipping fee.
def test_cart_total_member_shipping():
    c = cart.Cart()
    c.add_item("Pen", 5.0, quantity=10)   # subtotal 50 (no bulk discount)
    # no coupon
    expected_amount = 50
    shipping = cart.shipping_fee(expected_amount, member=True)
    total_expected = round(expected_amount + shipping, 2)
    assert c.total(member=True) == total_expected

# Empty cart: total is zero and shipping not charged.
def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0

# Edge case: subtotal after coupon equals free shipping threshold.
# In such a case shipping_fee should still be 0.
def test_cart_total_free_shipping_after_coupon():
    c = cart.Cart()
    # Set subtotal just below free threshold, then apply a coupon that takes it above threshold.
    c.add_item("ExpensiveItem", 950.0, quantity=1)   # subtotal 950
    assert c.subtotal() == 950.00
    # Coupon of 5% brings subtotal to 902.5 (still below). Need 10% to cross 1000.
    total = c.total(coupon="SAVE10")
    expected_amount = cart.apply_discount(950, 10)
    shipping = cart.shipping_fee(expected_amount)   # should be 0 because >= 1000 after discount
    assert total == round(expected_amount + shipping, 2)
    assert shipping == 0

# Verify rounding of totals: use values that lead to long decimals.
def test_cart_total_rounding():
    c = cart.Cart()
    c.add_item("Item", 33.333, quantity=3)   # subtotal 99.999
    expected_subtotal = round(99.999, 2)
    assert c.subtotal() == expected_subtotal
    total = c.total()
    # Shipping on 100 (rounded) => shipping_fee(100)=60
    # Total should be 160 rounded to 2 decimals
    assert total == round(expected_subtotal + cart.shipping_fee(expected_subtotal), 2)

# Test that subtotal uses rounding after applying discount.
def test_cart_subtotal_rounding_after_discount():
    c = cart.Cart()
    # Quantity triggers bulk discount of 5%
    c.add_item("Item", 33.333, quantity=12)   # line_total before discount: 399.996
    discounted = cart.apply_discount(399.996, 5)
    assert discounted == round(399.996 * (1 - 0.05), 2)
    assert c.subtotal() == round(discounted, 2)

# Verify that remove_item removes item if quantity goes to zero or negative.
def test_cart_remove_to_zero():
    c = cart.Cart()
    c.add_item("Apple", 1.0, quantity=3)
    c.remove_item("Apple", quantity=3)   # should remove entirely
    assert "Apple" not in c.items()
    with pytest.raises(KeyError):
        c.remove_item("Apple")   # already removed

# Verify that removing more than existing quantity deletes the item.
def test_cart_remove_more_than_existing():
    c = cart.Cart()
    c.add_item("Pear", 2.0, quantity=5)
    c.remove_item("Pear", quantity=10)   # should delete and not raise
    assert "Pear" not in c.items()

# Test that Cart.total uses shipping_fee based on amount after coupon.
def test_cart_total_shipping_on_amount_after_coupon():
    c = cart.Cart()
    c.add_item("Thing", 500.0, quantity=2)   # subtotal 1000 -> free shipping initially
    # Apply coupon of 10%: new amount is 900
    total = c.total(coupon="SAVE10")   # shipping should be applied to 900, not 1000
    expected_amount = cart.apply_discount(1000, 10)  # 900
    assert total == round(expected_amount + cart.shipping_fee(expected_amount), 2)
    # Verify that shipping fee is 60 for non-member in this scenario.
    assert cart.shipping_fee(expected_amount) == 60
