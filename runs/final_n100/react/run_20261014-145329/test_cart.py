import cart
import pytest

# ---------- apply_discount ----------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price, percent", [
    (-1, 10),   # negative price
    (100, -5),  # negative percent
    (100, 105), # percent > 100
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------

def test_bulk_discount_brackets():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@pytest.mark.parametrize("qty", [0, -5])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- parse_coupon ----------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20 ") == 20
    assert cart.parse_coupon("  SaVe5") == 5

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "DISCOUNT10", "SAVE-5", "SAVExx"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------

def test_shipping_free():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1200) == 0

def test_shipping_regular_and_member():
    assert cart.shipping_fee(500) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(500, member=True) == 30

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ----------

def test_cart_add_and_items():
    c = cart.Cart()
    assert list(c.items()) == []
    c.add_item("apple", 1.5, quantity=2)
    assert list(c.items()) == [("apple", (1.5, 2))]

def test_cart_remove_and_subtotal():
    c = cart.Cart()
    c.add_item("banana", 0.75, quantity=4)
    c.remove_item("banana", quantity=2)
    assert list(c.items()) == [("banana", (0.75, 2))]
    assert c.subtotal() == 1.5

def test_cart_total_without_discount():
    c = cart.Cart()
    c.add_item("book", 15.0, quantity=3)   # subtotal 45
    total = c.total(member=False)
    assert total == pytest.approx(45 + 60)  # shipping fee applied

def test_cart_total_with_member_and_bulk():
    c = cart.Cart()
    c.add_item("tshirt", 20.0, quantity=12)  # bulk discount 5%
    # expected price after bulk: 20*12=240 -> 5% off => 228
    subtotal_after_discount = 228
    total = c.total(member=True)
    # shipping fee for members is half (30) because subtotal < 1000
    assert total == pytest.approx(subtotal_after_discount + 30)

def test_cart_total_with_coupon_and_member():
    c = cart.Cart()
    c.add_item("hat", 40.0, quantity=1)  # subtotal 40
    total = c.total(member=True, coupon="SAVE10")
    # 10% off on subtotal => 36; shipping for members 30 -> total 66
    assert total == pytest.approx(36 + 30)

# ---------- Integration test: complex scenario ----------

def test_complex_scenario():
    c = cart.Cart()
    c.add_item("widget", 100.0, quantity=60)  # bulk discount 10%
    # original subtotal 6000; after 10% -> 5400
    # member shipping free (since subtotal > 1000)
    total = c.total(member=True)
    assert total == pytest.approx(5400)
