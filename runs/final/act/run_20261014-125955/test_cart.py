import pytest
import cart

# Helper to round for comparison

def almost_equal(a, b, eps=1e-9):
    return abs(a - b) < eps

# ---- apply_discount -----------------------------------------------------

def test_apply_discount_normal():
    assert cart.apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [-5, 101, 200])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---- bulk_discount_percent -----------------------------------------------

def test_bulk_discount_percent_cases():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(1500) == 15

@ pytest.mark.parametrize("quantity", [0, -1, -10])
def test_bulk_discount_percent_invalid_quantity_raises(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---- parse_coupon --------------------------------------------------------

def test_parse_coupon_valid_cases():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon(" SAVE30 ") == 30
    # boundary values
    assert cart.parse_coupon("SAVE1") == 1
    assert cart.parse_coupon("SAVE50") == 50

@ pytest.mark.parametrize("code", ["",
                                    "SAV10",
                                    "SAVE0",
                                    "SAVE51",
                                    "123",
                                    "SAVE-5",
                                    "  "])
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---- shipping_fee --------------------------------------------------------

def test_shipping_fee_free_over_threshold():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0

@ pytest.mark.parametrize("subtotal", [0, 500, 999])
def test_shipping_fee_nonfree(subtotal):
    # non-members
    assert cart.shipping_fee(subtotal, member=False) == 60
    # members pay half
    assert cart.shipping_fee(subtotal, member=True) == 30

@ pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Cart class ----------------------------------------------------------

def test_cart_basic_operations():
    c = cart.Cart()
    # Initially empty
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 60  # shipping fee non-member, no items

    # Add item
    c.add_item("Apple", unit_price=50, quantity=3)
    assert c.items()["Apple"] == (50, 3)
    assert c.subtotal() == 150
    assert c.total(member=True) == 120  # 150 subtotal + 30 shipping

    # Add another item same name increases quantity
    c.add_item("Apple", unit_price=50, quantity=2)
    assert c.items()["Apple"] == (50, 5)
    assert c.subtotal() == 250

    # Remove some quantity
    c.remove_item("Apple", quantity=3)
    assert c.items()["Apple"] == (50, 2)
    assert c.subtotal() == 100

    # Remove more than present -> should remove item entirely
    c.remove_item("Apple", quantity=5)
    assert "Apple" not in c.items()
    assert c.subtotal() == 0

    # Coupon application and bulk discount logic inside total()
    # Add a bulk case: 20 units of Banana price 10 each
    c.add_item("Banana", unit_price=10, quantity=20)
    # Bulk discount percent should be 5% for quantity 20
    expected_subtotal = 20 * 10 * (1 - 0.05)  # apply bulk discount
    assert almost_equal(c.subtotal(), expected_subtotal)
    # Now apply a coupon SAVE10 (10%) on top of subtotal
    total_with_coupon = c.total(member=False, coupon="SAVE10")
    # Shipping fee applies: subtotal < 1000 -> 60
    expected_total = expected_subtotal * 0.90 + 60
    assert almost_equal(total_with_coupon, expected_total)

# ---- Edge case: Coupon and bulk together ---------------------------------

def test_cart_bulk_and_coupon_interaction():
    c = cart.Cart()
    # Add 60 units of item price 5 each => bulk discount 10%
    c.add_item("ItemX", unit_price=5, quantity=60)
    subtotal_no_discount = 60 * 5
    bulk_pct = cart.bulk_discount_percent(60)  # should be 10
    discounted_subtotal = subtotal_no_discount * (1 - bulk_pct / 100)
    assert almost_equal(c.subtotal(), discounted_subtotal)
    # Apply coupon SAVE20 (20%) after bulk discount
    total = c.total(member=False, coupon="SAVE20")
    expected_total = discounted_subtotal * 0.80 + 60
    assert almost_equal(total, expected_expected:=expected_total)

# ---- Test that Cart.total uses shipping fee correctly when subtotal >=1000 -----

def test_cart_free_shipping():
    c = cart.Cart()
    c.add_item("Expensive", unit_price=500, quantity=3)  # subtotal 1500
    assert c.subtotal() == 1500
    # No shipping fee for members or non-members
    assert c.total(member=False) == 1500
    assert c.total(member=True) == 1500

# ---- Test that Cart.total raises error if coupon invalid ------

def test_cart_invalid_coupon_raises():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
