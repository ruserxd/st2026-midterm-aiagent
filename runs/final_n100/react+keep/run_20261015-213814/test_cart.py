import pytest
import cart

# ---------- apply_discount tests ----------

@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount_basic(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 20)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent tests ----------

@pytest.mark.parametrize("quantity,expected", [
    (99, 10),
    (50, 10),
    (49, 5),
    (10, 5),
    (9, 0),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, 3.5, "10"])
def test_bulk_discount_percent_invalid_raises(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon tests ----------

@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE5 ", 5),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", ["NOPE", "SAVE0", "SAVE51", "", "SAVE-1", 123])
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- Cart functionality tests (spec-compliant) ----------

@pytest.fixture
def simple_cart():
    c = cart.Cart()
    # 5 units of item A at $10 each => subtotal before discount: 50
    c.add_item("A", 10, 5)
    return c

# Test items dict

def test_items_dict(simple_cart):
    assert simple_cart.items() == {"A": 5}

# Subtotal with bulk discount for quantity=5 => no discount (0%)

def test_subtotal_no_discount(simple_cart):
    assert simple_cart.subtotal() == 50.00

# Add more items to trigger discount

def test_subtotal_with_bulk_discount():
    c = cart.Cart()
    # 10 units => bulk discount 5%
    c.add_item("B", 20, 10)
    expected_line_total = 20 * 10 * (1 - 0.05)  # 190
    assert c.subtotal() == round(expected_line_total, 2)

# Removing items

def test_remove_item_decrements_and_removes():
    c = cart.Cart()
    c.add_item("C", 5, 3)
    c.remove_item("C", 1)
    assert c.items() == {"C": 2}
    # remove remaining
    c.remove_item("C", 2)
    assert "C" not in c.items()

# Removing more than present should delete item

def test_remove_more_than_present():
    c = cart.Cart()
    c.add_item("D", 5, 1)
    with pytest.raises(KeyError):
        c.remove_item("E", 1)  # not in cart
    c.remove_item("D", 2)  # quantity > existing
    assert "D" not in c.items()

# Total calculation with coupon and shipping

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("E", 100, 1)
    # subtotal $100; apply 10% coupon => 90
    total_amount = c.total(coupon="SAVE10")
    assert total_amount == round(90 + 60, 2)  # shipping fee 60 for non-member

# Total should be zero for empty cart

def test_total_empty_cart():
    c = cart.Cart()
    assert c.total() == 0

# Shipping free over threshold (simulate by subtotal > 1000)

def test_shipping_free_over_threshold(monkeypatch):
    c = cart.Cart()
    c.add_item("F", 200, 6)  # $1200 subtotal
    assert c.total() == round(1200 + 0, 2)

# Test member shipping half fee

def test_member_shipping_half_fee():
    c = cart.Cart()
    c.add_item("G", 20, 1)  # subtotal 20
    assert c.total(member=True) == round(20 + 30, 2)  # shipping 60/2=30
