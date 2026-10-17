import pytest
import cart

# ----- apply_discount tests -----

@pytest.mark.parametrize("price,percent,expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (100, 100, 0.0),
    # rounding to two decimals
    (123.45, 25, 92.59),
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price,percent", [
    (-1, 10),   # negative price
    (100, -5),  # negative percent
    (100, 105), # percent >100
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ----- bulk discount percent tests -----

@pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
    (150, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 2.5, "10"])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ----- coupon parsing tests -----

valid_coupons = [
    ("SAVE10", 10),
    ("save20", 20),          # case-insensitive
    (" SAVE30 ", 30),        # whitespace trimmed
]

@pytest.mark.parametrize("code,expected", valid_coupons)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

invalid_coupons = [
    "",
    "SAVEX",
    "SAVE0",
    "SAVE51",
    "ABCD10",
    "SAVE10abc",
    None,
]

@pytest.mark.parametrize("code", invalid_coupons)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ----- shipping fee tests -----

def test_shipping_fee():
    # negative subtotal
    with pytest.raises(ValueError):
        cart.shipping_fee(-1)
    # below threshold
    assert cart.shipping_fee(999) == 60
    # at threshold and above
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1200) == 0
    # member discount half
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(900, member=True) == 30
    # at threshold with membership still free
    assert cart.shipping_fee(1000, member=True) == 0

# ----- Cart class tests -----

def test_cart_initial_state():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.0
    assert c.total() == 0

def test_add_item_and_subtotal():
    c = cart.Cart()
    c.add_item("apple", 10, 3)
    assert c.items() == {"apple": 3}
    # No bulk discount for quantity 3
    assert c.subtotal() == 30.0
    # Total with shipping fee (non-member)
    assert c.total() == 90.0   # subtotal 30 + shipping 60

def test_add_item_increase_and_price_error():
    c = cart.Cart()
    c.add_item("banana", 5, 2)
    c.add_item("banana", 5, 1)
    assert c.items()["banana"] == 3
    with pytest.raises(ValueError):
        c.add_item("banana", 6, 1)   # mismatched unit price

def test_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("pear")

def test_remove_item_zero_removal_bug():
    c = cart.Cart()
    c.add_item("orange", 20, 2)
    c.remove_item("orange", 1)
    assert c.items()["orange"] == 1
    c.remove_item("orange", 1)
    # Spec requires item to be removed; implementation may leave it with quantity 0.
    assert "orange" not in c.items()

def test_remove_more_than_quantity():
    c = cart.Cart()
    c.add_item("pear", 5, 2)
    c.remove_item("pear", 3)   # removes the item
    assert c.items() == {}

# Bulk discount calculation in subtotal

def test_subtotal_with_bulk_discounts():
    c = cart.Cart()
    # No bulk for quantity 9
    c.add_item("itemA", 10, 9)
    # 5% bulk for quantity 10
    c.add_item("itemB", 5, 10)
    # subtotal: 10*9=90 (no discount) + 5*10=50 with 5% => 47.5
    assert c.subtotal() == 137.5
    # total without shipping yet should be subtotal+shipping
    expected_total = 137.5 + 60  # shipping fee for subtotal<1000
    assert c.total() == expected_total

# Total with coupon and shipping bug detection

def test_total_with_coupon_and_shipping_bug():
    c = cart.Cart()
    # Create a subtotal >= 1000 so original shipping would be free if bug exists
    c.add_item("expensive", 200, 6)   # 1200 total before discount
    # Apply coupon of 20% off -> discounted amount 960 < 1000
    assert c.subtotal() == 1200.0
    # Expected shipping based on discounted amount: fee 60
    expected_total = 960 + 60
    assert c.total(coupon="SAVE20") == expected_total

# Invalid coupon raises ValueError in total

def test_total_with_invalid_coupon():
    c = cart.Cart()
    c.add_item("item", 10, 1)
    with pytest.raises(ValueError):
        c.total(coupon="SAVE200")

# Total with membership shipping discount

def test_total_member_shipping():
    c = cart.Cart()
    c.add_item("book", 50, 5)   # subtotal 250
    assert c.subtotal() == 250.0
    assert c.total(member=True) == 280.0   # 250 + 30 shipping

# Empty cart no shipping fee

def test_empty_cart_no_shipping():
    c = cart.Cart()
    assert c.total() == 0
