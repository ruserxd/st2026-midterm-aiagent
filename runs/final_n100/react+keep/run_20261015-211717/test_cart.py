import pytest
import cart

# --- apply_discount -------------------------------------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

def test_apply_discount_boundaries_and_errors():
    # valid boundaries
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(100, 100) == 0.0

    # invalid inputs
    with pytest.raises(ValueError):
        cart.apply_discount(-1, 10)
    with pytest.raises(ValueError):
        cart.apply_discount(50, -5)
    with pytest.raises(ValueError):
        cart.apply_discount(50, 105)

# --- bulk_discount_percent -----------------------------------------------------

def test_bulk_discount_percent_branches():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

def test_bulk_discount_percent_invalid():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-5)

# --- parse_coupon --------------------------------------------------------------

def test_parse_coupon_valid_codes():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20 ") == 20
    assert cart.parse_coupon(" SAVE50") == 50
    assert cart.parse_coupon("  SaVe15   ") == 15

def test_parse_coupon_invalid():
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVEX5")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE0")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE51")
    with pytest.raises(ValueError):
        cart.parse_coupon("   ")

# --- shipping_fee --------------------------------------------------------------

def test_shipping_fee_free_and_reduced():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(500, member=True) == 30

def test_shipping_fee_invalid_subtotal():
    with pytest.raises(ValueError):
        cart.shipping_fee(-10)

# --- Cart class ---------------------------------------------------------------

def test_cart_initial_state_and_basic_methods():
    c = cart.Cart()
    assert c.items() == []
    assert c.subtotal() == 0
    assert c.total() == 0

    # add item and check items list structure
    c.add_item("apple", unit_price=200, quantity=3)
    assert c.items() == [("apple", 200, 3)]
    assert c.subtotal() == 600
    assert c.total() == 660  # 600 + shipping fee 60

    # remove item partially
    c.remove_item("apple", quantity=1)
    assert c.items() == [("apple", 200, 2)]
    assert c.subtotal() == 400

    # add another item
    c.add_item("banana", unit_price=100)
    assert c.items() == [("apple", 200, 2), ("banana", 100, 1)]
    assert c.subtotal() == 500

    # member flag reduces shipping fee but not subtotal
    assert c.total(member=True) == 530

    # apply coupon before shipping
    assert c.total(coupon="SAVE10") == pytest.approx(445)

# --- helper tests to inspect implementation details (not part of spec) ----------

# Not required for specification compliance, but useful for debugging.
def test_cart_total_logic_output():
    import inspect, textwrap
    src = inspect.getsource(cart.Cart.total)
    # Just printing the source so that if we run tests, it appears in output.
    print(textwrap.dedent(src))
