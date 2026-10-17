import pytest
import cart

# ---------------------------------------------------------------------------
# apply_discount
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("price, percent, expected", [
    (200, 15, 170.0),
    (123.456, 10, 111.11),
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@pytest.mark.parametrize("price", [ -5, -1 ])
def test_apply_discount_invalid_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-1, 101, 150])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# Edge cases for percent boundaries
@pytest.mark.parametrize("price, percent, expected", [
    (50, 0, 50.0),
    (80, 100, 0.0),
])
def test_apply_discount_edge_percent(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# ---------------------------------------------------------------------------
# bulk_discount_percent
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("quantity, expected", [
    (5, 0),
    (10, 5),
    (50, 10),
    (100, 15),
    (101, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -3])
def test_bulk_discount_invalid_quantity_zero_or_negative(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

@pytest.mark.parametrize("quantity", [10.5, "20", None])
def test_bulk_discount_non_integer(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------------------------------------------------------------------------
# parse_coupon
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("code, expected", [
    ("SAVE10", 10),
    ("save1", 1),
    ("   SAVE50   ", 50),
    ("SaVe25", 25),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVE0",
    "SAVE51",
    "SAVEB0",
    "NOTCUPON",
    "SAVExx",
    " ",
    "",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------------------------------------------------------------------------
# shipping_fee
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("subtotal, member, expected", [
    (999.99, False, 60),
    (999.99, True, 30),
    (1000, False, 0),
    (1000, True, 0),
    (1500, False, 0),
    (1500, True, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-10.5, -1])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------------------------------------------------------------------------
# Cart class tests
# ---------------------------------------------------------------------------
def test_cart_initially_empty():
    c = cart.Cart()
    assert isinstance(c.items(), dict)
    assert len(c.items()) == 0
    assert c.subtotal() == 0
    assert c.total() == 0

# add_item and quantity update
def test_add_new_item_and_quantity_update():
    c = cart.Cart()
    c.add_item("apple", 2.5, 3)
    assert c.items() == {"apple": 3}
    # Add same item with same unit price
    c.add_item("apple", 2.5, 2)
    assert c.items() == {"apple": 5}

# add_item with invalid unit_price or quantity
@pytest.mark.parametrize("unit_price, quantity", [(-1.0, 2), (1.0, 0)])
def test_add_item_invalid_unit_or_quantity(unit_price, quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("orange", unit_price, quantity)

# add_item with price mismatch
def test_add_item_price_mismatch():
    c = cart.Cart()
    c.add_item("apple", 2.5, 1)
    with pytest.raises(ValueError):
        c.add_item("apple", 3.0, 1)

# remove_item tests
def test_remove_partial_and_full():
    c = cart.Cart()
    c.add_item("pear", 4.0, 5)
    c.remove_item("pear", 2)
    assert c.items() == {"pear": 3}
    c.remove_item("pear", 3)  # remove remaining
    assert "pear" not in c.items()

def test_remove_more_than_existing():
    c = cart.Cart()
    c.add_item("grape", 1.0, 2)
    c.remove_item("grape", 5)  # should remove entirely
    assert "grape" not in c.items()

def test_remove_nonexistent_raises_keyerror():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent")

# subtotal tests
def test_subtotal_simple_no_discount():
    c = cart.Cart()
    c.add_item("item1", 10.0, 5)  # qty <10 -> no discount
    assert c.subtotal() == 50.0

def test_subtotal_with_discounts_and_rounding():
    c = cart.Cart()
    c.add_item("itemA", 2.0, 10)   # bulk 5%
    c.add_item("itemB", 3.0, 100)  # bulk 15%
    # itemA: pre=20 -> discount 1.0 -> subtotal 19.00
    # itemB: pre=300 -> discount 45.00 -> subtotal 255.00
    assert c.subtotal() == 274.0

def test_subtotal_rounding_example():
    c = cart.Cart()
    c.add_item("roundItem", 0.99, 12)  # qty >=10 -> bulk 5%
    # pre=11.88; discount 0.594 -> subtotal 11.286 -> round to 2 decimals => 11.29
    assert c.subtotal() == 11.29

def test_subtotal_empty():
    c = cart.Cart()
    assert c.subtotal() == 0

# total tests
@pytest.mark.parametrize("member", [False, True])
def test_total_with_coupon_and_shipping(member):
    c = cart.Cart()
    # Items totaling 1000 before discount
    c.add_item("expensive", 500.0, 2)
    expected_total = 900 + (30 if member else 60)  # 10% coupon -> 900; shipping applied
    assert c.total(member=member, coupon="SAVE10") == expected_total

def test_total_coupon_only_no_shipping_over_1000():
    c = cart.Cart()
    c.add_item("item", 500.0, 3)  # subtotal 1500
    # Apply 20% coupon -> 1200; shipping free (>=1000)
    assert c.total(member=False, coupon="SAVE20") == 1200

def test_total_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item("item", 100.0, 1)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")

# Test that coupon pushing subtotal below free threshold triggers shipping
def test_total_coupon_pushes_below_free_threshold():
    c = cart.Cart()
    c.add_item("item", 200.0, 6)  # subtotal 1200
    expected = 1200 * 0.8 + 60  # 20% coupon -> 960 < 1000 => shipping 60
    assert c.total(member=False, coupon="SAVE20") == expected

def test_total_empty_cart_zero():
    c = cart.Cart()
    assert c.total() == 0
    assert c.total(member=True) == 0
    assert c.total(coupon="SAVE10") == 0
