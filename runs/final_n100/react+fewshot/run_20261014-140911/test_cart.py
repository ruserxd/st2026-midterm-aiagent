import pytest
import cart

# Helper fixture for a fresh cart instance
@pytest.fixture
def new_cart():
    return cart.Cart()

# ---------- apply_discount -------------------------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

def test_apply_discount_rounding():
    # 3% off of 333 -> 323.01 after rounding to 2 decimals
    expected = round(333 * 0.97, 2)
    assert cart.apply_discount(333, 3) == expected

def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        cart.apply_discount(-1, 10)

def test_apply_discount_invalid_percent():
    for p in (-5, 105):
        with pytest.raises(ValueError):
            cart.apply_discount(100, p)

# ---------- bulk_discount_percent ------------------------------------------

def test_bulk_discount_no_discount():
    assert cart.bulk_discount_percent(9) == 0

def test_bulk_discount_small():
    assert cart.bulk_discount_percent(10) == 5

def test_bulk_discount_medium():
    assert cart.bulk_discount_percent(50) == 10

def test_bulk_discount_large():
    assert cart.bulk_discount_percent(100) == 15

def test_bulk_discount_invalid_quantity():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)

# ---------- parse_coupon -----------------------------------------------------

def test_parse_coupon_valid_basic():
    assert cart.parse_coupon("SAVE10") == 10

def test_parse_coupon_case_insensitive_and_whitespace():
    assert cart.parse_coupon("  save20  ") == 20

def test_parse_coupon_invalid_format():
    for code in ["DISCOUNT", "SAVE", "SAVExx", "SAVE0", "SAVE51"]:
        with pytest.raises(ValueError):
            cart.parse_coupon(code)

# ---------- shipping_fee -----------------------------------------------------

def test_shipping_free_for_high_subtotal():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500.5) == 0

def test_shipping_regular_non_member():
    assert cart.shipping_fee(200) == 60

def test_shipping_member_half():
    assert cart.shipping_fee(300, member=True) == 30

def test_shipping_invalid_subtotal():
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

# ---------- Cart class -------------------------------------------------------

def test_cart_add_and_items(new_cart):
    c = new_cart
    c.add_item("Apple", 1.5, quantity=2)
    c.add_item("Banana", 0.75)  # default quantity 1
    assert c.items() == {
        "Apple": (1.5, 2),
        "Banana": (0.75, 1),
    }

def test_cart_remove_item_partial(new_cart):
    c = new_cart
    c.add_item("Orange", 0.8, quantity=3)
    c.remove_item("Orange", quantity=2)
    assert c.items() == {"Orange": (0.8, 1)}

def test_cart_remove_item_full(new_cart):
    c = new_cart
    c.add_item("Grape", 2.0, quantity=5)
    c.remove_item("Grape")  # default removes one unit
    assert c.items() == {"Grape": (2.0, 4)}

def test_cart_remove_more_than_present_raises(new_cart):
    c = new_cart
    c.add_item("Peach", 3.0, quantity=2)
    with pytest.raises(ValueError):
        c.remove_item("Peach", quantity=5)

def test_cart_subtotal(new_cart):
    c = new_cart
    c.add_item("Item1", 10, quantity=3)   # 30
    c.add_item("Item2", 5, quantity=4)    # 20
    assert c.subtotal() == 50

def test_cart_total_without_discount(new_cart):
    c = new_cart
    c.add_item("Book", 15, quantity=2)
    expected = 30.0 + cart.shipping_fee(30)
    assert c.total(member=False, coupon=None) == expected

def test_cart_total_with_bulk_and_member_coupon(new_cart):
    # 5 items of the same kind -> bulk discount 5%
    c = new_cart
    c.add_item("T-shirt", 20, quantity=5)  # subtotal 100
    # coupon SAVE10 gives 10% off after bulk discount
    base = 100
    bulk_disc = cart.bulk_discount_percent(5)
    discounted_after_bulk = cart.apply_discount(base, bulk_disc)
    final_before_shipping = cart.apply_discount(discounted_after_bulk, 10)
    shipping = cart.shipping_fee(final_before_shipping)
    expected_total = round(final_before_shipping + shipping, 2)
    assert c.total(member=True, coupon="SAVE10") == expected_total
