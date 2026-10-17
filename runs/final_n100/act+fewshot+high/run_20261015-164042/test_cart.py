import pytest
import cart

# 1. apply_discount
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
    (99.99, 10, 89.99),
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# 2. bulk_discount_percent
@pytest.mark.parametrize("qty,expected", [
    (9,0),
    (10,5),
    (49,5),
    (50,10),  # bug: expected 10 but implementation returns 5
    (51,10),
    (99,10),
    (100,15),
])
def test_bulk_discount_percent(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected

@pytest.mark.parametrize("qty", [0,-1,3.5,"a"])
def test_bulk_discount_percent_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# 3. parse_coupon
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),          # spec: case-insensitive
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("invalid_code", ["SAV10","SAVE0","SAVE51","SAVEabc"])
def test_parse_coupon_invalid(invalid_code):
    with pytest.raises(ValueError):
        cart.parse_coupon(invalid_code)

# 4. shipping_fee
@pytest.mark.parametrize("subtotal,member,expected", [
    (500, False, 60),
    (500, True, 30),
    (1000, False, 0),
    (999.99, False, 60),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1,-10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# 5. Cart.add_item
def test_cart_add_new_item():
    c = cart.Cart()
    c.add_item("Apple", 1.0)
    assert c.items() == {"Apple": 1}

def test_cart_add_increment_quantity():
    c = cart.Cart()
    c.add_item("Book", 10, 2)
    c.add_item("Book", 10, 3)
    assert c.items() == {"Book": 5}

def test_cart_add_different_price_error():
    c = cart.Cart()
    c.add_item("Book", 10, 1)
    with pytest.raises(ValueError):
        c.add_item("Book", 12, 1)

@pytest.mark.parametrize("unit_price,quantity", [(-1,1),(5,-1)])
def test_cart_add_invalid(unit_price, quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("Apple", unit_price, quantity)

# 6. Cart.remove_item
def test_cart_remove_partial():
    c = cart.Cart()
    c.add_item("Pen", 1.5, 3)
    c.remove_item("Pen", 1)
    assert c.items() == {"Pen": 2}

def test_cart_remove_exact_removal():
    c = cart.Cart()
    c.add_item("Pen", 1.5, 2)
    c.remove_item("Pen", 2)
    # Spec: item should be removed completely
    assert "Pen" not in c.items()

def test_cart_remove_more_than_exists():
    c = cart.Cart()
    c.add_item("Pen", 1.5, 3)
    c.remove_item("Pen", 5)   # quantity after removal negative; item should be deleted
    assert "Pen" not in c.items()

def test_cart_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("NonExistent")

# 7. Cart.subtotal
def test_cart_subtotal_empty():
    c = cart.Cart()
    assert c.subtotal() == 0

def test_cart_subtotal_with_discount():
    c = cart.Cart()
    c.add_item("Book", 10, 3)   # subtotal 30
    c.add_item("Pen", 1.5, 12)  # line_total=18; bulk discount percent 5%
    expected_line = round(18 * (100 - 5) / 100, 2)
    expected_subtotal = 30 + expected_line
    assert c.subtotal() == expected_subtotal

# 8. Cart.total
def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0

def test_cart_total_no_coupon():
    c = cart.Cart()
    c.add_item("Book", 20, 5)   # subtotal 100
    expected_non_member = round(100 + 60, 2)
    expected_member = round(100 + 30, 2)
    assert c.total(member=False) == expected_non_member
    assert c.total(member=True) == expected_member

def test_cart_total_cross_threshold():
    c = cart.Cart()
    c.add_item("Expensive", 300, 4)   # subtotal 1200 (>=1000)
    # No coupon total
    assert c.total() == round(1200 + 0, 2)
    # Coupon that brings amount below free shipping threshold
    discounted = cart.apply_discount(1200, 20)   # expected 960
    expected_non_member = round(discounted + 60, 2)
    expected_member = round(discounted + 30, 2)
    assert c.total(member=False, coupon="SAVE20") == expected_non_member
    assert c.total(member=True, coupon="SAVE20") == expected_member

def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("Book", 10, 1)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")
