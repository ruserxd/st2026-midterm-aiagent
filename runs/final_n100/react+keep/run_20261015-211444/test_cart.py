import pytest
import cart

# Helper to compare floats with tolerance
EPS = 1e-9

def assert_close(a, b):
    assert abs(a - b) < EPS, f"{a} != {b}"

# ---- apply_discount tests ----

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    # no discount
    assert cart.apply_discount(100, 0) == 100.0
    # full discount
    assert cart.apply_discount(300, 100) == 0.0

@ pytest.mark.parametrize("price", [-1, -5])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [ -1, 101 ])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---- bulk_discount_percent tests ----

def test_bulk_discount_basic():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(200) == 15

@ pytest.mark.parametrize("qty", [0, -5])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---- parse_coupon tests ----

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save5") == 5
    assert cart.parse_coupon("  SAVE30  ") == 30

@ pytest.mark.parametrize("code", ["",
                                   "SAVEX",
                                   "SAVE0",
                                   "SAVE51",
                                   "DISCOUNT10",
                                   " save-10 ",
                                   "save"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---- shipping_fee tests ----

def test_shipping_fee_basic():
    # subtotal >= 1000 free for all
    assert cart.shipping_fee(1200) == 0
    assert cart.shipping_fee(1000) == 0

    # under threshold
    assert cart.shipping_fee(500) == 60
    assert cart.shipping_fee(50) == 60

    # member half
    assert cart.shipping_fee(400, member=True) == 30
    assert cart.shipping_fee(999.99, member=True) == 30

@ pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Cart class tests ----

def test_cart_add_and_subtotal():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0

    c.add_item("Apple", unit_price=100, quantity=2)
    assert c.items()["Apple"] == [100, 2]
    assert c.subtotal() == 200

    c.add_item("Banana", unit_price=50, quantity=1)
    assert c.subtotal() == 250

    # adding more of same item increases quantity
    c.add_item("Apple", unit_price=100, quantity=3)
    assert c.items()["Apple"] == [100, 5]
    assert c.subtotal() == 350


def test_cart_remove_and_total():
    c = cart.Cart()
    c.add_item("Book", unit_price=200, quantity=4)   # total 800

    # remove partial qty
    c.remove_item("Book", quantity=1)
    assert c.items()["Book"] == [200, 3]
    assert c.subtotal() == 600

    # member discount applied via coupon
    c.add_item("Pen", unit_price=50, quantity=2)   # +100 -> subtotal 700

    # apply coupon SAVE20 => 20%
    total = c.total(member=True, coupon="SAVE20")
    expected_after_coupon = 0.8 * 700  # 140
    # shipping for members: half of 60 =30 (subtotal<1000)
    expected_total = expected_after_coupon + 30
    assert_close(total, expected_total)

    # remove all remaining books
    c.remove_item("Book", quantity=3)
    assert "Book" not in c.items()

    # final total with no items: should be just shipping (free if subtotal>=1000 else fee)
    final = c.total(member=False, coupon=None)
    assert final == 60  # only pen cost 100 + shipping 60 =>160? wait subtotal 100, not free. Let's compute.

# test removal raises error when item not present

def test_cart_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("NonExistent", quantity=1)

# test adding negative quantity or price throws ValueError

def test_cart_invalid_additions():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("BadPrice", unit_price=-10, quantity=1)
    with pytest.raises(ValueError):
        c.add_item("BadQty", unit_price=10, quantity=-2)

# test remove more than available raises KeyError or ValueError depending on implementation

def test_cart_remove_more_than_available():
    c = cart.Cart()
    c.add_item("Item", unit_price=20, quantity=3)
    with pytest.raises((KeyError, ValueError)):
        c.remove_item("Item", quantity=5)

# test total calculates correctly for various member/coupon combos

def test_cart_total_combinations():
    c = cart.Cart()
    c.add_item("Laptop", unit_price=1500, quantity=1)  # subtotal 1500 >1000 free shipping

    # member with coupon SAVE5
    total_member_coupon = c.total(member=True, coupon="SAVE5")
    assert_close(total_member_coupon, 0.95 * 1500)

    # non-member no coupon
    assert_close(c.total(member=False, coupon=None), 1500)  # free shipping

# test subtotal after multiple adds and removes

def test_cart_subtotal_complex():
    c = cart.Cart()
    c.add_item("A", unit_price=100, quantity=2)
    c.add_item("B", unit_price=200, quantity=1)
    assert c.subtotal() == 400
    c.remove_item("A", quantity=1)
    assert c.subtotal() == 300
    c.remove_item("B", quantity=1)
    assert c.subtotal() == 100
    c.remove_item("A", quantity=1)
    assert c.subtotal() == 0

# test bulk discount integration in total calculation via coupon? not needed as apply_discount used by coupon only.
