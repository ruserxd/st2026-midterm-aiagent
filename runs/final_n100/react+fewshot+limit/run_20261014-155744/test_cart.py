import pytest
import cart

# ---------- apply_discount -------------------------------------------------

def test_apply_discount_valid():
    assert cart.apply_discount(200, 15) == 170.0
    # rounding to 2 decimals
    assert cart.apply_discount(99.999, 10) == round(99.999 * 0.90, 2)

@pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 20)

@pytest.mark.parametrize("percent", [-5, 110])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent ------------------------------------------

def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    # According to specification, quantity >=50 gives 10%
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

@pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon -----------------------------------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20 ") == 20
    assert cart.parse_coupon("  SaVe5") == 5

@pytest.mark.parametrize("code", ["SAVEE", "SAVE0", "SAVE51", "DISCOUNT10", "123"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee -----------------------------------------------------

def test_shipping_fee():
    # free shipping for subtotal >= 1000
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1001) == 0
    # member pays half when not free
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(999, member=False) == 60

@pytest.mark.parametrize("subtotal", [-10, -0.01])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart functionality ----------------------------------------------

@pytest.fixture
def empty_cart():
    return cart.Cart()

def test_add_item_new(empty_cart):
    empty_cart.add_item("apple", 1.0, quantity=2)
    assert empty_cart.items() == {"apple": 2}

def test_add_item_existing_same_price(empty_cart):
    empty_cart.add_item("banana", 0.5, quantity=3)
    empty_cart.add_item("banana", 0.5, quantity=2)
    assert empty_cart.items() == {"banana": 5}

def test_add_item_invalid_price(empty_cart):
    with pytest.raises(ValueError):
        empty_cart.add_item("orange", -1.0, quantity=1)

def test_add_item_invalid_quantity(empty_cart):
    with pytest.raises(ValueError):
        empty_cart.add_item("grape", 2.0, quantity=0)

def test_add_item_price_mismatch(empty_cart):
    empty_cart.add_item("melon", 3.0, quantity=1)
    with pytest.raises(ValueError):
        empty_cart.add_item("melon", 4.0, quantity=1)

def test_remove_item():
    c = cart.Cart()
    c.add_item("item", 10, quantity=5)
    c.remove_item("item", quantity=3)
    assert c.items() == {"item": 2}
    # removing remaining qty removes item
    c.remove_item("item", quantity=2)
    assert c.items() == {}

def test_remove_item_not_present(empty_cart):
    with pytest.raises(KeyError):
        empty_cart.remove_item("nonexistent")

# ---------- subtotal calculation -------------------------------------------

def test_subtotal_single_item_no_discount():
    c = cart.Cart()
    c.add_item("book", 20, quantity=2)
    # no bulk discount
    assert c.subtotal() == round(20 * 2, 2)  # 40.00

def test_subtotal_with_bulk_discount():
    c = cart.Cart()
    # quantity 10 - 5% discount on that item's subtotal
    c.add_item("pen", 1.0, quantity=10)
    expected = round(1.0 * 10 * (1 - 0.05), 2)  # 9.50
    assert c.subtotal() == expected

# ---------- total calculation ---------------------------------------------

def test_total_no_coupon_no_member():
    c = cart.Cart()
    c.add_item("shoes", 300, quantity=1)
    # subtotal 300, no coupon, shipping fee 60 - total 360
    assert c.total() == round(300 + 60, 2)

def test_total_with_coupon():
    c = cart.Cart()
    c.add_item("watch", 500, quantity=1)
    # subtotal 500, coupon SAVE10 reduces to 450, shipping 60 - total 510
    assert c.total(coupon="SAVE10") == round(500 * 0.90 + 60, 2)

def test_total_with_member_and_coupon():
    c = cart.Cart()
    c.add_item("laptop", 1500, quantity=1)
    # subtotal 1500, coupon SAVE20 - 1200, shipping free - total 1200
    assert c.total(member=True, coupon="SAVE20") == round(1500 * 0.80 + 0, 2)

def test_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0

# ---------- invalid coupon passed to total ---------------------------------

def test_total_invalid_coupon_raises(empty_cart):
    with pytest.raises(ValueError):
        empty_cart.total(coupon="INVALID")
