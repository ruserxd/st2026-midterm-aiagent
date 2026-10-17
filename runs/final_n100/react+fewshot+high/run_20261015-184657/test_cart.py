import pytest
import cart

def test_apply_discount_normal():
    assert cart.apply_discount(200, 15) == 170.0

def test_apply_discount_percent_limits():
    assert cart.apply_discount(100, 100) == 0.0
    assert cart.apply_discount(123.45, 0) == 123.45

@pytest.mark.parametrize("percent", [-1, 101])
def test_apply_discount_percent_out_of_bounds(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(50, percent)

def test_bulk_discount_percent_boundaries():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

@pytest.mark.parametrize("quantity", [0, -1, "10", 3.5])
def test_bulk_discount_percent_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("SAVE10", 10),
        ("save20", 20),
        ("   SAVE5   ", 5),
        ("SaVe50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    [
        "DISCOUNT10",
        "SAVE0",
        "SAVE51",
        "SAVE-5",
        "",
        "  ",
        "SAVE10ABC",
    ],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

@pytest.mark.parametrize(
    ("subtotal", "member", "expected"),
    [
        (1000, False, 0),
        (1500, True, 0),
        (999.99, False, 60),
        (800, True, 30),
        (500, False, 60),
        (-10, False, None),   # expects ValueError
    ],
)
def test_shipping_fee(subtotal, member, expected):
    if subtotal < 0:
        with pytest.raises(ValueError):
            cart.shipping_fee(subtotal, member)
    else:
        assert cart.shipping_fee(subtotal, member) == expected

def test_cart_add_new_item():
    c = cart.Cart()
    c.add_item("Apple", 1.0, 3)
    assert c.items() == {"Apple": 3}

def test_cart_add_existing_same_price_increments_quantity():
    c = cart.Cart()
    c.add_item("Banana", 0.5, 2)
    c.add_item("Banana", 0.5, 4)
    assert c.items() == {"Banana": 6}

def test_cart_add_existing_different_price_error():
    c = cart.Cart()
    c.add_item("Orange", 1.2, 3)
    with pytest.raises(ValueError):
        c.add_item("Orange", 1.5, 1)

def test_cart_negative_unit_price_error():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("Grapes", -0.3, 2)

@pytest.mark.parametrize("quantity", [0, -5, "10", 3.14])
def test_cart_invalid_quantity_error(quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("Peach", 1.0, quantity)

def test_cart_remove_partial():
    c = cart.Cart()
    c.add_item("Watermelon", 2.5, 4)
    c.remove_item("Watermelon", 2)
    assert c.items() == {"Watermelon": 2}

def test_cart_remove_to_zero_removes():
    c = cart.Cart()
    c.add_item("Kiwi", 0.8, 3)
    c.remove_item("Kiwi", 3)   # quantity equals existing
    assert "Kiwi" not in c.items()

def test_cart_remove_nonexistent_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("NonExisting", 1)

def test_cart_items_structure():
    c = cart.Cart()
    c.add_item("Mango", 1.5, 2)
    assert set(c.items().keys()) == {"Mango"}
    assert isinstance(c.items()["Mango"], int)

def test_cart_subtotal_single_item_no_bulk_discount():
    c = cart.Cart()
    c.add_item("Pear", 3.0, 4)
    assert c.subtotal() == 12.0

def test_cart_subtotal_with_bulk_discount():
    c = cart.Cart()
    c.add_item("Cherry", 2.0, 10) # 20 before discount -> 19 after 5%
    assert c.subtotal() == 19.0

def test_cart_subtotal_multiple_items():
    c = cart.Cart()
    c.add_item("Cherry", 2.0, 10) # subtotal 19
    c.add_item("Berry", 3.0, 6)    # subtotal 18
    assert c.subtotal() == 37.0

def test_cart_subtotal_empty_returns_zero():
    c = cart.Cart()
    assert c.subtotal() == 0

def test_cart_total_without_coupon_and_shipping_fee_non_member():
    c = cart.Cart()
    c.add_item("Book", 20.0, 6)   # subtotal 120
    expected_subtotal = 120.0
    expected_shipping = 60
    assert c.total() == round(expected_subtotal + expected_shipping, 2)

def test_cart_total_without_coupon_member_half_shipping():
    c = cart.Cart()
    c.add_item("Book", 20.0, 6)   # subtotal 120
    assert c.total(member=True) == round(120 + 30, 2)

def test_cart_total_with_coupon_below_threshold():
    c = cart.Cart()
    c.add_item("Expensive", 1100.0, 1)
    expected_subtotal_before = 1100.0
    coupon_percent = 10
    discounted_amount = cart.apply_discount(expected_subtotal_before, coupon_percent)  # 990
    expected_total = round(discounted_amount + 60, 2)
    assert c.total(coupon="SAVE10") == expected_total

def test_cart_total_invalid_coupon_error():
    c = cart.Cart()
    c.add_item("Item", 10, 1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

def test_cart_total_empty_cart_zero():
    c = cart.Cart()
    assert c.total() == 0

def test_cart_subtotal_rounding():
    c = cart.Cart()
    c.add_item("RoundItem", 3.333, 3)   # subtotal before discount 9.999
    assert c.subtotal() == round(3.333*3, 2)
