import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# ---------- apply_discount ----------

def test_apply_discount_basic():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(50, 100) == 0.0

@pytest.mark.parametrize("price,percent", [(-1, 10), (10, -5), (10, 105)])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        apply_discount(price, percent)

# ---------- bulk_discount_percent ----------

def test_bulk_discount_percent():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@pytest.mark.parametrize("quantity", [0, -3])
def test_bulk_discount_percent_errors(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon ----------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20") == 20
    assert parse_coupon(" SAVE30 ") == 30

@pytest.mark.parametrize(
    "code",
    ["SAVExx", "ABC10", "SAVE0", "SAVE51", "   ", "12345"]
)
def test_parse_coupon_errors(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee ----------

def test_shipping_fee():
    assert shipping_fee(1200) == 0
    assert shipping_fee(999.99) == 60
    assert shipping_fee(1000) == 0
    assert shipping_fee(0, member=True) == 30
    assert shipping_fee(500, member=False) == 60

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_errors(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart class ----------

def test_cart_basic_operations():
    cart = Cart()
    assert cart.items() == {}
    cart.add_item("apple", 100, quantity=2)
    cart.add_item("banana", 50)
    assert cart.items() == {
        "apple": (100, 2),
        "banana": (50, 1),
    }

    # subtotal calculation
    assert cart.subtotal() == 100 * 2 + 50 * 1

    # total without member or coupon
    expected = 250 + shipping_fee(250)
    assert cart.total() == expected

    # adding more quantity updates correctly
    cart.add_item("apple", 100, quantity=3)  # now 5 apples
    assert cart.items()["apple"] == (100, 5)
    assert cart.subtotal() == 100 * 5 + 50

    # remove item partially
    cart.remove_item("apple", quantity=2)  # 3 left
    assert cart.items()["apple"] == (100, 3)
    cart.remove_item("banana")
    assert "banana" not in cart.items()

    # total with member discount and coupon
    expected_sub = cart.subtotal() * 0.9  # 10% off
    expected_total = expected_sub + shipping_fee(expected_sub, member=True)
    assert cart.total(member=True, coupon="SAVE10") == pytest.approx(expected_total)

# ---------- Cart add_item error handling ----------

def test_cart_add_item_errors():
    cart = Cart()
    with pytest.raises(ValueError):
        cart.add_item("item", -5)
    with pytest.raises(ValueError):
        cart.add_item("item", 10, quantity=0)

# ---------- Cart remove_item errors ----------

def test_cart_remove_item_errors():
    cart = Cart()
    cart.add_item("item", 20, quantity=1)
    with pytest.raises(ValueError):
        cart.remove_item("nonexistent")
    with pytest.raises(ValueError):
        cart.remove_item("item", quantity=-3)
