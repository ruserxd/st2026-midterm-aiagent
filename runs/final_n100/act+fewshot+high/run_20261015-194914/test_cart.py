import pytest
import cart

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(99.99, 33) == 66.99
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(100, 100) == 0.0

@pytest.mark.parametrize("price,percent", [
    (-10,20),
    (10,-5),
    (10,150)
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)


def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    # This should return 10 for quantity=50 according to spec,
    # but the implementation incorrectly returns 5.
    assert cart.bulk_discount_percent(50) == 10

@pytest.mark.parametrize("quantity", [0, -1])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)


def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    # Case-insensitive coupon codes should be accepted.
    assert cart.parse_coupon("save10") == 10
    assert cart.parse_coupon(" SAVE50 ") == 50

@pytest.mark.parametrize("code", ["SAVE0", "SAVEXYZ", "123SAVE", 42])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)


def test_shipping_fee():
    # Subtotal less than threshold
    assert cart.shipping_fee(0, False) == 60
    assert cart.shipping_fee(999.9, True) == 30.0
    # Exactly at threshold
    assert cart.shipping_fee(1000, False) == 0
    assert cart.shipping_fee(1000, True) == 0


def test_shipping_fee_negative():
    with pytest.raises(ValueError):
        cart.shipping_fee(-1, False)

# Cart tests

def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item("Apple", 10, 5)
    assert c.items() == {"Apple": 5}
    c.add_item("Apple", 10, 3)
    assert c.items() == {"Apple": 8}
    c.add_item("Banana", 2, 1)
    assert c.items() == {"Apple": 8, "Banana": 1}


def test_cart_add_invalid():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("Orange", -5, 1)
    with pytest.raises(ValueError):
        c.add_item("Orange", 5, 0)
    with pytest.raises(ValueError):
        c.add_item("Orange", 5, "two")


def test_cart_remove_reduce():
    c = cart.Cart()
    c.add_item("Apple", 10, 5)
    c.remove_item("Apple", 3)
    assert c.items() == {"Apple": 2}
    with pytest.raises(KeyError):
        c.remove_item("Banana", 1)


def test_cart_remove_exact_quantity():
    c = cart.Cart()
    c.add_item("Apple", 10, 5)
    c.remove_item("Apple", 5)
    assert "Apple" not in c.items()


def test_cart_remove_more_than_quantity():
    c = cart.Cart()
    c.add_item("Apple", 10, 2)
    c.remove_item("Apple", 5)  # should delete
    assert c.items() == {}


def test_cart_subtotal_no_discount():
    c = cart.Cart()
    c.add_item("Apple", 10, 5)   # no bulk discount
    assert c.subtotal() == 50


def test_cart_subtotal_with_bulk():
    c = cart.Cart()
    c.add_item("Orange", 20, 12)   # bulk_discount_percent(12)=5
    expected = round(20 * 12 * (100 - 5) / 100, 2)
    assert c.subtotal() == expected


def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0


def test_cart_total_without_coupon_member_false():
    c = cart.Cart()
    c.add_item("Apple", 10, 5)   # subtotal=50
    assert c.total(member=False) == round(50 + 60, 2)


def test_cart_total_without_coupon_member_true():
    c = cart.Cart()
    c.add_item("Apple", 10, 5)
    assert c.total(member=True) == round(50 + 30.0, 2)


def test_cart_total_with_coupon_member_false():
    c = cart.Cart()
    c.add_item("Apple", 10, 5)
    # coupon SAVE20 => 20% discount
    assert c.total(coupon="SAVE20") == round(round(50 * 0.8, 2) + 60, 2)


def test_cart_total_with_coupon_member_true():
    c = cart.Cart()
    c.add_item("Apple", 10, 5)
    assert c.total(member=True, coupon="SAVE20") == round(round(50 * 0.8, 2) + 30.0, 2)


def test_cart_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("Apple", 10, 5)
    with pytest.raises(ValueError):
        c.total(coupon="INVALID")


def test_cart_total_cross_threshold_no_member():
    c = cart.Cart()
    # Subtotal >1000 before coupon
    c.add_item("Expensive", 200, 6)   # 1200 subtotal
    expected_after_discount = round(1200 * 0.8, 2)
    shipping_fee_expected = 60
    expected_total = round(expected_after_discount + shipping_fee_expected, 2)
    assert c.total(coupon="SAVE20") == expected_total


def test_cart_total_cross_threshold_member():
    c = cart.Cart()
    c.add_item("Expensive", 200, 6)   # 1200 subtotal
    shipping_fee_expected = 30.0
    expected_after_discount = round(1200 * 0.8, 2)
    expected_total = round(expected_after_discount + shipping_fee_expected, 2)
    assert c.total(member=True, coupon="SAVE20") == expected_total
