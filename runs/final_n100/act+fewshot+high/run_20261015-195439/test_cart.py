import cart
import pytest

# ---------- Apply Discount ----------
@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200.0, 15, 170.0),
        (101.0, 33, 67.67),
        (99.99, 10, 89.99),
        (99.999, 10, 90.0),
        (123.456, 25, 92.59),
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == pytest.approx(expected)

@pytest.mark.parametrize(
    "price, percent",
    [
        (-10, 20),
        (50, -5),
        (30, 105),
    ],
)
def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- Bulk Discount Percent ----------
@pytest.mark.parametrize(
    "quantity, expected",
    [
        (9, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (200, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -5, 2.5],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- Parse Coupon ----------
@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        ("save20", 20),
        (" SAVE1 ", 1),
        ("sAvE50", 50),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    ["save0", "SAVE51", "INVALID", "", "SAVExx", "123"],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- Shipping Fee ----------
@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (0, False, 60),
        (999.99, False, 60),
        (1000, False, 0),
        (1500, False, 0),
        (0, True, 30),
        (999.99, True, 30),
        (1000, True, 0),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-10, -1],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart Operations ----------
def test_cart_add_and_subtotal():
    c = cart.Cart()
    # Initially empty subtotal should be 0
    assert c.subtotal() == 0

    c.add_item("Apple", 1.5, quantity=2)
    assert c.items() == {"Apple": 2}
    assert c.subtotal() == pytest.approx(3.0)

    # Add same item with same price -> quantity increases
    c.add_item("Apple", 1.5, quantity=3)
    assert c.items() == {"Apple": 5}
    assert c.subtotal() == pytest.approx(7.5)

    # Adding different item
    c.add_item("Banana", 0.75, quantity=4)
    assert c.items() == {"Apple": 5, "Banana": 4}
    expected = 5 * 1.5 + 4 * 0.75
    assert c.subtotal() == pytest.approx(expected)

def test_cart_add_invalid():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("Apple", -1, quantity=2)
    with pytest.raises(ValueError):
        c.add_item("Apple", 1.5, quantity=-3)

    # Adding same name with different price
    c.add_item("Orange", 0.9, quantity=1)
    with pytest.raises(ValueError):
        c.add_item("Orange", 1.0, quantity=2)

def test_cart_remove_item():
    c = cart.Cart()
    c.add_item("Milk", 2.0, quantity=5)
    # Remove part of the quantity
    c.remove_item("Milk", quantity=3)
    assert c.items() == {"Milk": 2}
    assert c.subtotal() == pytest.approx(4.0)

    # Remove remaining (or more) to remove item completely
    c.remove_item("Milk", quantity=5)
    assert "Milk" not in c.items()
    assert c.subtotal() == 0

def test_cart_remove_invalid():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("Eggs", quantity=1)

# ---------- Cart Total ----------
def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == pytest.approx(0.00)

def test_cart_total_simple():
    c = cart.Cart()
    c.add_item("Book", 12.99, quantity=1)
    # Subtotal 12.99 + shipping 60 => total 72.99
    assert c.total() == pytest.approx(72.99)

def test_cart_total_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("Pen", 5.0, quantity=10)          # subtotal = 50
    total_value = c.total(member=False, coupon="SAVE10")
    # Discount 10% => 45; shipping 60 => total 105
    assert total_value == pytest.approx(105.0)

def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("Item", 10, quantity=1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

def test_cart_total_member_shipping_half():
    c = cart.Cart()
    # subtotal 400
    c.add_item("Gadget", 200.0, quantity=2)
    total_non_member = c.total(member=False)
    total_member = c.total(member=True)

    assert total_non_member == pytest.approx(460.0)   # 400 + 60
    assert total_member == pytest.approx(430.0)       # 400 + 30

def test_cart_total_free_shipping():
    c = cart.Cart()
    c.add_item("Expensive", 600, quantity=2)
    # subtotal 1200 >= 1000 => free shipping
    assert c.total() == pytest.approx(1200.0)

def test_cart_total_rounding():
    c = cart.Cart()
    c.add_item("Precise", 10/3, quantity=1)   # price ~3.333...
    total_value = c.total()
    expected = round((10/3) + 60, 2)
    assert total_value == pytest.approx(expected)

def test_cart_total_discount_affects_shipping():
    c = cart.Cart()
    c.add_item("Luxury", 1200, quantity=1)
    # subtotal 1200, coupon SAVE50 => discounted subtotal 600
    total_value = c.total(coupon="SAVE50")
    # shipping fee computed on discounted subtotal (<1000) -> 60
    assert total_value == pytest.approx(660.0)

def test_cart_total_discount_and_member_shipping_half():
    c = cart.Cart()
    c.add_item("Luxury", 1200, quantity=1)
    total_value = c.total(member=True, coupon="SAVE50")
    # discounted subtotal 600 <1000 -> shipping half 30 => total 630
    assert total_value == pytest.approx(630.0)
