import pytest
import cart

# -------------------- apply_discount ---------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize(
    "price,percent,expected",
    [
        (100, 0, 100.0),
        (50, 100, 0.0),
        (123.45, 12.5, round(123.45 * 0.875, 2)),
    ],
)
def test_apply_discount_various(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

# boundary and error cases
@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize(
    "percent", ["fifty", -5, 105]
)
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# -------------------- bulk_discount_percent ---------------------------------

def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(100) == 15

@pytest.mark.parametrize("quantity", [0, -3, 2.5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# -------------------- parse_coupon ---------------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon(" save20 ") == 20
    assert cart.parse_coupon("SaVe5") == 5

@pytest.mark.parametrize(
    "code",
    ["", "DISCOUNT10", "SAVE0", "SAVE51", "SAVExx", "NOPE", None],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# -------------------- shipping_fee ---------------------------------

def test_shipping_fee():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0

    # member discount half
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(1200, member=True) == 0

@pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# -------------------- Cart class ---------------------------------

def test_cart_initially_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

# add_item and items

def test_add_and_items():
    c = cart.Cart()
    c.add_item("apple", 1.5, 3)
    c.add_item("banana", 0.8, 2)
    assert c.items() == {"apple": 3, "banana": 2}

# adding same item with same price increases quantity

def test_add_same_item_increases_quantity():
    c = cart.Cart()
    c.add_item("widget", 10.0, 1)
    c.add_item("widget", 10.0, 4)
    assert c.items()["widget"] == 5

# adding same item with different price raises ValueError

def test_add_same_item_different_price_error():
    c = cart.Cart()
    c.add_item("gadget", 5.0)
    with pytest.raises(ValueError):
        c.add_item("gadget", 6.0)

# remove_item functionality

def test_remove_item_reduce_and_delete():
    c = cart.Cart()
    c.add_item("thing", 2.0, 3)
    c.remove_item("thing", 1)
    assert c.items()["thing"] == 2
    c.remove_item("thing", 2)
    assert "thing" not in c.items()

# removing non-existent item raises KeyError

def test_remove_nonexistent_raises():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("missing")

# subtotal calculation with bulk discounts

def test_subtotal_bulk_discount():
    c = cart.Cart()
    # 9 units -> no discount
    c.add_item("a", 10.0, 9)
    assert c.subtotal() == round(90.0, 2)
    # 10 units -> 5% discount on that line
    c.remove_item("a", 9)  # keep 1 more to make 10 total
    c.add_item("a", 10.0, 1)
    assert c.subtotal() == round(100.0 * 0.95, 2)

# total with coupon and shipping

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("item", 200.0, 5)  # subtotal 1000 -> no bulk discount
    assert c.subtotal() == 1000.0
    # member with coupon SAVE10
    total = c.total(member=True, coupon="SAVE10")
    expected = round(1000 * 0.9 + cart.shipping_fee(1000, member=True), 2)
    assert total == expected

# total without shipping when subtotal is zero (empty cart)
def test_total_empty_no_shipping():
    c = cart.Cart()
    assert c.total() == 0

# invalid coupon raises ValueError during total

def test_total_invalid_coupon_raises():
    c = cart.Cart()
    c.add_item("x", 10.0, 1)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")
