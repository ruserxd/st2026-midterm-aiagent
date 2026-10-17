import pytest
import cart

# ---------- apply_discount ----------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price,percent,result", [
    (100, 0, 100.00),
    (50, 100, 0.00),
])
def test_apply_discount_boundaries(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price,percent", [
    (-10, 20),
    (100, -5),
    (100, 105),
])
def test_apply_discount_errors(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---------- bulk_discount_percent ----------

def test_bulk_discount_boundary_quantities():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

@pytest.mark.parametrize("quantity", [0, -1])
def test_bulk_discount_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon ----------

def test_parse_coupon_valid_cases():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon("  SaVe30 ") == 30

@pytest.mark.parametrize("code", ["",
                                   "SAVE0",
                                   "SAVE51",
                                   "INVALID",
                                   "SAVE-5",
                                   "SAVEE10",
])
def test_parse_coupon_errors(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ----------

def test_shipping_fee_free_and_paid():
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(200) == 60

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class behavior ----------

def test_cart_initially_empty():
    c = cart.Cart()
    assert c.items() == {}
    assert c.subtotal() == 0.00
    assert c.total() == 0.00

# Adding items

def test_add_item_basic_and_increment():
    c = cart.Cart()
    c.add_item("apple", 1.50, 2)
    assert c.items() == {"apple": 2}
    # Add same item with same price
    c.add_item("apple", 1.50, 3)
    assert c.items() == {"apple": 5}


def test_add_item_price_mismatch():
    c = cart.Cart()
    c.add_item("banana", 0.99, 1)
    with pytest.raises(ValueError):
        c.add_item("banana", 1.00, 2)

# Invalid add parameters
@pytest.mark.parametrize("name,price,qty", [
    ("orange", -0.5, 1),
    ("pear", 0.5, 0),
    ("grape", 0.3, -2),
])
def test_add_item_invalid_params(name, price, qty):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item(name, price, qty)

# Removing items

def test_remove_item_partial_and_full():
    c = cart.Cart()
    c.add_item("mango", 2.00, 5)
    c.remove_item("mango", 3)
    assert c.items() == {"mango": 2}
    # remove more than remaining to trigger removal
    c.remove_item("mango", 5)
    assert c.items() == {}

def test_remove_nonexistent_item():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent", 1)

# Items dict should not expose internal data

def test_items_return_new_dict():
    c = cart.Cart()
    c.add_item("kiwi", 0.75, 4)
    d = c.items()
    d["kiwi"] = 10  # modify copy
    assert c.items()["kiwi"] == 4

# Subtotal calculation with bulk discounts and rounding

def test_subtotal_with_bulk_discount():
    c = cart.Cart()
    c.add_item("itemA", 100, 9)   # <10 -> no discount
    c.add_item("itemB", 50, 10)   # >=10 =>5% discount
    # subtotal before discounts: 900 + 500 = 1400
    # discount on itemB: 5% of 500 = 25, so adjusted B = 475
    # total = 900 + 475 = 1375.00
    assert c.subtotal() == 1375.00

# Total with coupon and shipping fee, rounding

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("widget", 200, 1)
    # subtotal = 200
    # apply SAVE10 -> 180
    # shipping for non-member on 180 < 1000 => 60
    # total = 240.00
    assert c.total(coupon="SAVE10") == 240.00

# Total with member discount and free shipping threshold

def test_total_member_and_free_shipping():
    c = cart.Cart()
    c.add_item("premium", 1000, 1)
    # subtotal=1000; coupon SAVE20 -> 800; shipping on 800 non-member? but member=True gives half
    # shipping fee for 800 <1000 => 60; member pays 30
    # total = 800 + 30 = 830.00
    assert c.total(member=True, coupon="SAVE20") == 830.00

# Total empty cart returns 0 without shipping

def test_total_empty_cart_no_shipping():
    c = cart.Cart()
    assert c.total() == 0.00
