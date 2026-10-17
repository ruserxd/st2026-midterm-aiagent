import pytest
import cart

# ---------- apply_discount tests ----------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@ pytest.mark.parametrize(
    "price,percent,expected",
    [
        (100, 0, 100.0),
        (100, 100, 0.0),
        (123.456, 20, round(98.7648,2)),
    ],
)
def test_apply_discount_variants(price, percent, expected):
    assert cart.apply_discount(price, percent) == expected

@ pytest.mark.parametrize("price", [-1, -100])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@ pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent tests ----------

def test_bulk_discount_bounds():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@ pytest.mark.parametrize("qty", [0, -5])
def test_bulk_discount_invalid_qty(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- parse_coupon tests ----------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon("  SaVe30 ") == 30

@ pytest.mark.parametrize("code", ["DISCOUNT", "SAVE0", "SAVE51", "SA VE5", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee tests ----------

def test_shipping_fee_free_and_half():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(5000, member=True) == 30
    assert cart.shipping_fee(1001, member=False) == 60

@ pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart tests ----------

def test_cart_add_and_items():
    c = cart.Cart()
    assert c.items() == {}
    c.add_item("apple", 1.5, 3)
    assert c.items() == {"apple": 3}
    # adding same item increases quantity
    c.add_item("apple", 1.5, 2)
    assert c.items() == {"apple": 5}

@ pytest.mark.parametrize("unit_price", [-1, -0.01])
def test_cart_add_negative_unit(unit_price):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("banana", unit_price, 2)

@ pytest.mark.parametrize("qty", [0, -3])
def test_cart_add_invalid_qty(qty):
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("orange", 2.0, qty)

def test_cart_add_price_mismatch():
    c = cart.Cart()
    c.add_item("pear", 2.5, 1)
    with pytest.raises(ValueError):
        c.add_item("pear", 3.0, 1)

# remove_item tests

def test_cart_remove_and_removal():
    c = cart.Cart()
    c.add_item("mango", 4.0, 5)
    c.remove_item("mango", 2)
    assert c.items() == {"mango": 3}
    # remove more than remaining
    c.remove_item("mango", 5)
    assert c.items() == {}

def test_cart_remove_nonexistent():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("peach", 1)

# subtotal tests

def test_subtotal_with_discounts_and_rounding():
    c = cart.Cart()
    # 9 items -> no discount, 10 items -> 5%
    c.add_item("itemA", 10.0, 9)
    c.add_item("itemB", 20.0, 10)  # 5% off
    expected_A = 10.0 * 9  # 90.0
    expected_B = 20.0 * 10 * (1 - 0.05)  # 190.0
    assert c.subtotal() == round(expected_A + expected_B, 2)

# total tests with coupon and shipping

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("book", 30.0, 20)  # 10% bulk discount -> 27.0 each
    subtotal = 27.0 * 20  # 540.0
    # coupon SAVE5 -> 5%
    after_coupon = subtotal * (1 - 0.05)
    shipping = cart.shipping_fee(after_coupon, member=False)  # >1000? no => 60
    total_expected = round(after_coupon + shipping, 2)
    assert c.total(coupon="SAVE5") == total_expected

# empty cart cost zero and no shipping

def test_empty_cart_total():
    c = cart.Cart()
    assert c.total() == 0.0
    # also with member and coupon should still be 0
    assert c.total(member=True, coupon="SAVE10") == 0.0
