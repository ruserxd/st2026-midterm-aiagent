import pytest
import cart

def _apply_discount_manual(price: float, percent: int) -> float:
    return round(price * (1 - percent / 100), 2)

def _bulk_discount_percent_manual(quantity: int) -> int:
    if quantity >= 100:
        return 15
    elif quantity >= 50:
        return 10
    elif quantity >= 10:
        return 5
    else:
        return 0

def _shipping_fee_manual(subtotal: float, member: bool = False) -> float:
    if subtotal >= 1000:
        return 0.0
    return 30.0 if member else 60.0

# apply_discount tests
def test_apply_discount_valid():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(99.99, 5) == _apply_discount_manual(99.99, 5)

@pytest.mark.parametrize("price,percent", [
    (-10, 20),
    (100, -1),
    (100, 101),
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent tests
def test_bulk_discount_percent_valid():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

@pytest.mark.parametrize("quantity", [0, -1, 3.5])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize("code,expected", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVExx",
    "DISCOUNT5",
    "SAVE0",
    "SAVE51",
    "",
    "   ",
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

def test_parse_coupon_returns_int():
    assert isinstance(cart.parse_coupon("SAVE5"), int)

# shipping_fee tests
def test_shipping_fee_valid():
    assert cart.shipping_fee(1000) == 0.0
    assert cart.shipping_fee(999.99) == 60.0
    assert cart.shipping_fee(999.99, member=True) == 30.0
    assert cart.shipping_fee(1500) == 0.0

def test_shipping_fee_negative():
    with pytest.raises(ValueError):
        cart.shipping_fee(-1)

# Cart tests
def test_cart_add_item_and_items():
    c = cart.Cart()
    c.add_item("apple", 1.00, quantity=2)
    assert c.items() == {"apple": 2}
    d = c.items()
    d["apple"] = 5
    assert c.items()["apple"] == 2

def test_cart_add_existing_item():
    c = cart.Cart()
    c.add_item("apple", 1.00, quantity=2)
    c.add_item("apple", 1.00, quantity=3)
    assert c.items() == {"apple": 5}

def test_cart_add_item_different_price():
    c = cart.Cart()
    c.add_item("apple", 1.00, quantity=2)
    with pytest.raises(ValueError):
        c.add_item("apple", 2.00, quantity=1)

def test_cart_add_negative_unit_price():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("banana", -1.0, quantity=1)

@pytest.mark.parametrize("quantity", [0, -3, 2.5])
def test_cart_add_invalid_quantity(quantity):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("orange", 1.0, quantity=quantity)

def test_cart_remove_item_partial_and_complete():
    c = cart.Cart()
    c.add_item("apple", 1.00, quantity=5)
    c.remove_item("apple", 1)
    assert c.items()["apple"] == 4
    c.remove_item("apple", 10)
    assert "apple" not in c.items()

def test_cart_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent", 1)

def test_cart_add_default_quantity():
    c = cart.Cart()
    c.add_item("apple", 2.0)  # default quantity 1
    assert c.items() == {"apple": 1}

def test_cart_remove_default_quantity():
    c = cart.Cart()
    c.add_item("banana", 3.0, quantity=2)
    c.remove_item("banana")  # remove 1 (default)
    assert c.items()["banana"] == 1
    c.remove_item("banana")  # remove last one
    assert "banana" not in c.items()

def test_cart_subtotal_multiple_items():
    c = cart.Cart()
    c.add_item("apple", 1.00, quantity=10)   # bulk discount 5%
    c.add_item("banana", 2.50, quantity=51) # bulk discount 10%
    c.add_item("cherry", 3.00, quantity=105)# bulk discount 15%
    expected = (
        _apply_discount_manual(1.00 * 10, _bulk_discount_percent_manual(10)) +
        _apply_discount_manual(2.50 * 51, _bulk_discount_percent_manual(51)) +
        _apply_discount_manual(3.00 * 105, _bulk_discount_percent_manual(105))
    )
    expected = round(expected, 2)
    assert c.subtotal() == expected

def test_cart_subtotal_empty():
    c = cart.Cart()
    assert c.subtotal() == 0

@pytest.fixture
def sample_cart():
    c = cart.Cart()
    c.add_item("apple", 1.00, quantity=10)
    c.add_item("banana", 2.50, quantity=51)
    c.add_item("cherry", 3.00, quantity=105)
    return c

def test_cart_total_no_coupon_non_member(sample_cart):
    subtotal = sample_cart.subtotal()
    expected = round(subtotal + _shipping_fee_manual(subtotal, member=False), 2)
    assert sample_cart.total(member=False) == expected

def test_cart_total_no_coupon_member(sample_cart):
    subtotal = sample_cart.subtotal()
    expected = round(subtotal + _shipping_fee_manual(subtotal, member=True), 2)
    assert sample_cart.total(member=True) == expected

def test_cart_total_with_coupon_non_member(sample_cart):
    subtotal = sample_cart.subtotal()
    discounted = _apply_discount_manual(subtotal, 10)
    shipping = _shipping_fee_manual(discounted, member=False)
    expected = round(discounted + shipping, 2)
    assert sample_cart.total(member=False, coupon="SAVE10") == expected

def test_cart_total_with_coupon_member(sample_cart):
    subtotal = sample_cart.subtotal()
    discounted = _apply_discount_manual(subtotal, 10)
    shipping = _shipping_fee_manual(discounted, member=True)
    expected = round(discounted + shipping, 2)
    assert sample_cart.total(member=True, coupon="SAVE10") == expected

def test_cart_total_invalid_coupon(sample_cart):
    with pytest.raises(ValueError):
        sample_cart.total(coupon="BAD")

def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0
    assert c.total(member=True) == 0
    # coupon on empty cart should still give 0, no shipping
    assert c.total(coupon="SAVE10") == 0

@pytest.fixture
def high_price_cart():
    c = cart.Cart()
    c.add_item("expensive", 200.0, quantity=6)
    return c

def test_high_price_no_coupon(high_price_cart):
    subtotal = high_price_cart.subtotal()  # should be 1200.0
    expected = round(subtotal + _shipping_fee_manual(subtotal), 2)
    assert high_price_cart.total() == expected

def test_high_price_with_coupon(high_price_cart):
    discounted = _apply_discount_manual(1200, 20)  # 960
    shipping = _shipping_fee_manual(discounted, member=False)
    expected = round(discounted + shipping, 2)
    assert high_price_cart.total(coupon="SAVE20") == expected

def test_high_price_with_coupon_member(high_price_cart):
    discounted = _apply_discount_manual(1200, 20)  # 960
    shipping = _shipping_fee_manual(discounted, member=True)
    expected = round(discounted + shipping, 2)
    assert high_price_cart.total(member=True, coupon="SAVE20") == expected
