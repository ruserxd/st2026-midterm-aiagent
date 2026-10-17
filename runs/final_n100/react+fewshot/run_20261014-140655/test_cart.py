import pytest
import cart

# ---------- apply_discount ----------

def test_apply_discount_normal():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent ----------

def test_bulk_discount_percent_below_10():
    assert cart.bulk_discount_percent(9) == 0

def test_bulk_discount_percent_10_to_49():
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(25) == 5
    assert cart.bulk_discount_percent(49) == 5

def test_bulk_discount_percent_50_to_99():
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(75) == 10
    assert cart.bulk_discount_percent(99) == 10

def test_bulk_discount_percent_100_and_above():
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@pytest.mark.parametrize("quantity", [0, -3, 2.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon(" SAVE30 ") == 30

@pytest.mark.parametrize("code", ["", "SAVEXX", "SAVE0", "SAVE51", "XYZ10"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------

def test_shipping_fee_free():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500, member=True) == 0

def test_shipping_fee_standard_non_member():
    assert cart.shipping_fee(500) == 60
    assert cart.shipping_fee(999.99) == 60

def test_shipping_fee_member_discount():
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(200, member=True) == 30

@pytest.mark.parametrize("subtotal", [-1, -50])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ----------

def test_cart_initial_state():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

def test_add_item_and_subtotal():
    c = cart.Cart()
    c.add_item("apple", 2.5, quantity=4)
    assert c.items()["apple"] == (2.5, 4)
    assert c.subtotal() == 10.0
    # Add more of same item with same unit price
    c.add_item("apple", 2.5, quantity=1)
    assert c.items()["apple"] == (2.5, 5)
    assert c.subtotal() == 12.5


def test_add_item_invalid_price_and_quantity():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("banana", -1, quantity=3)
    with pytest.raises(ValueError):
        c.add_item("banana", 1.0, quantity=-2)
    with pytest.raises(ValueError):
        c.add_item("banana", 1.0, quantity=0)

def test_add_item_price_mismatch():
    c = cart.Cart()
    c.add_item("orange", 3.0, quantity=2)
    with pytest.raises(ValueError):
        c.add_item("orange", 4.0, quantity=1)

# removal tests

def test_remove_item_and_total():
    c = cart.Cart()
    c.add_item("milk", 3.0, quantity=2)
    c.remove_item("milk", quantity=1)
    assert c.items()["milk"] == (3.0, 1)
    assert c.subtotal() == 3.0
    # remove remaining
    c.remove_item("milk")
    assert "milk" not in c.items()
    assert c.subtotal() == 0

# total with member and coupon

def test_total_member_and_coupon():
    c = cart.Cart()
    c.add_item("book", 120, quantity=1)
    # subtotal 120, shipping fee 60 -> 180
    # apply 10% discount via coupon SAVE10
    total = c.total(member=True, coupon="SAVE10")
    # shipping for member: 30, subtotal after discount: 108
    assert pytest.approx(total, rel=1e-9) == 138.0

# coupon parsing failure in total

def test_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("pen", 5)
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# removing more than exists should raise ValueError

def test_remove_more_than_exists():
    c = cart.Cart()
    c.add_item("hat", 20, quantity=1)
    with pytest.raises(ValueError):
        c.remove_item("hat", quantity=2)
