import pytest
import cart

# ---------- helper fixtures ----------
@pytest.fixture
def empty_cart():
    return cart.Cart()

@pytest.fixture
def sample_cart(empty_cart):
    c = empty_cart
    # add a few items with various quantities for bulk discount tests
    c.add_item("apple", 5.00, quantity=3)   # no discount
    c.add_item("banana", 2.50, quantity=12)  # 5% discount (>=10)
    c.add_item("cherry", 1.00, quantity=55)  # 10% discount (>=50)
    return c

# ---------- tests for utility functions ----------

def test_apply_discount_valid():
    assert cart.apply_discount(200.0, 15) == 170.0
    assert cart.apply_discount(100.0, 0) == 100.0
    assert cart.apply_discount(50.0, 100) == 0.0

with pytest.raises(ValueError):
    cart.apply_discount(-10, 20)
with pytest.raises(ValueError):
    cart.apply_discount(100, -5)
with pytest.raises(ValueError):
    cart.apply_discount(100, 105)


def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    # Spec says >=50 gives 10%
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15
with pytest.raises(ValueError):
    cart.bulk_discount_percent(-1)
with pytest.raises(ValueError):
    cart.bulk_discount_percent(0)


def test_parse_coupon_valid():
    # Spec: case‑insensitive and whitespace ignored
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon(" SAVE30 ") == 30

with pytest.raises(ValueError):
    cart.parse_coupon("SAVE0")   # below 1%
with pytest.raises(ValueError):
    cart.parse_coupon("SAVE51")  # above 50%
with pytest.raises(ValueError):
    cart.parse_coupon("NOTACODE")


def test_shipping_fee():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    # member half fee
    assert cart.shipping_fee(200, member=True) == 30

with pytest.raises(ValueError):
    cart.shipping_fee(-1)

# ---------- tests for Cart class behaviour ----------

def test_cart_add_and_items(empty_cart):
    c = empty_cart
    assert c.items() == {}
    c.add_item("widget", 10.0, quantity=2)
    assert c.items() == {"widget": 2}
    # adding same item increments quantity; price must match
    c.add_item("widget", 10.0, quantity=3)
    assert c.items() == {"widget": 5}
    with pytest.raises(ValueError):
        c.add_item("widget", 12.0)  # mismatched unit_price
    with pytest.raises(ValueError):
        c.add_item("gadget", -5.0)
    with pytest.raises(ValueError):
        c.add_item("gadget", 5.0, quantity=0)


def test_cart_remove_item(sample_cart):
    c = sample_cart
    # remove some quantity but not all
    c.remove_item("banana", quantity=5)
    assert c.items()["banana"] == 7
    # removing a single apple leaves one remaining
    c.remove_item("apple")
    assert c.items()["apple"] == 2
    # removing more than existing removes item entirely
    c.remove_item("cherry", quantity=55)
    assert "cherry" not in c.items()
    with pytest.raises(KeyError):
        c.remove_item("nonexistent")


def test_cart_subtotal(sample_cart):
    c = sample_cart
    # compute expected subtotal manually
    # apple: 5.00*3 = 15.00 (no discount)
    # banana: 2.50*12=30.00 - bulk_discount_percent(12)=5% -> 28.50
    # cherry: 1.00*55=55.00 - bulk_discount_percent(55)=10% -> 49.50
    expected = round(15.00 + 28.50 + 49.50, 2)
    assert c.subtotal() == expected


def test_cart_total_no_coupon_member(sample_cart):
    c = sample_cart
    subtotal = c.subtotal()
    total = c.total(member=True)
    # shipping_fee on amount after coupon (none) = 60 (member ->30)
    expected_total = round(subtotal + 30, 2)
    assert total == expected_total


def test_cart_total_with_coupon(sample_cart):
    c = sample_cart
    subtotal = c.subtotal()
    # apply coupon SAVE10 = 10% off subtotal
    after_coupon = cart.apply_discount(subtotal, cart.parse_coupon("SAVE10"))
    shipping = cart.shipping_fee(after_coupon)
    expected = round(after_coupon + shipping, 2)
    assert c.total(coupon="SAVE10") == expected


def test_cart_total_empty():
    c = cart.Cart()
    assert c.subtotal() == 0
    assert c.total() == 0
    assert c.total(member=True) == 0

# ---------- tests for edge cases and error handling ----------

def test_invalid_coupon_in_total(sample_cart):
    with pytest.raises(ValueError):
        sample_cart.total(coupon="INVALID")
