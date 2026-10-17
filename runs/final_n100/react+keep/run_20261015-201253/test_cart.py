import cart
import pytest

def expect_error(callable_, *args, **kwargs):
    try:
        callable_(*args, **kwargs)
    except Exception as e:
        return e
    raise AssertionError("Expected exception but none raised")

# 1. apply_discount tests

def test_apply_discount_valid():
    assert cart.apply_discount(200, 15) == 170.0
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0

@ pytest.mark.parametrize("price", [ -1, -10])
@ pytest.mark.parametrize("percent", [20])
def test_apply_discount_price_negative(price, percent):
    e = expect_error(cart.apply_discount, price, percent)
    assert isinstance(e, ValueError)

@ pytest.mark.parametrize("price", [10])
@ pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_percent_invalid(price, percent):
    e = expect_error(cart.apply_discount, price, percent)
    assert isinstance(e, ValueError)

# 2. bulk_discount_percent tests

def test_bulk_discount_percent_cases():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    # According to specification, 50 should return 10
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

def test_bulk_discount_percent_invalid():
    e = expect_error(cart.bulk_discount_percent, -1)
    assert isinstance(e, ValueError)
    e2 = expect_error(cart.bulk_discount_percent, 0.5)
    assert isinstance(e2, ValueError)

# 3. parse_coupon tests

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    # Leading/trailing whitespace should be ignored
    assert cart.parse_coupon("  save20 ") == 20
    assert cart.parse_coupon("SaVe1") == 1

@ pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "SAVEE5", "SAVE-5", "SAVED"])
def test_parse_coupon_invalid(code):
    e = expect_error(cart.parse_coupon, code)
    assert isinstance(e, ValueError)

# 4. shipping_fee tests

def test_shipping_fee_free_and_half():
    # free for >=1000
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0
    # half for members
    assert cart.shipping_fee(900, member=True) == 30
    # full for non-member
    assert cart.shipping_fee(900, member=False) == 60

def test_shipping_fee_invalid_subtotal():
    e = expect_error(cart.shipping_fee, -10)
    assert isinstance(e, ValueError)

# 5. Cart functionality

def test_cart_add_and_items():
    c = cart.Cart()
    c.add_item("apple", 2.0, 3)
    assert c.items() == {"apple": 3}
    c.add_item("apple", 2.0, 2)
    assert c.items() == {"apple": 5}


def test_cart_add_price_mismatch():
    c = cart.Cart()
    c.add_item("orange", 1.5, 1)
    e = expect_error(c.add_item, "orange", 2.0, 1)
    assert isinstance(e, ValueError)


def test_cart_remove_and_negative_quantity():
    c = cart.Cart()
    c.add_item("banana", 0.5, 4)
    c.remove_item("banana", 2)
    assert c.items() == {"banana": 2}
    # remove more than existing: should drop to zero and delete
    c.remove_item("banana", 3)
    assert "banana" not in c.items()


def test_cart_remove_nonexistent():
    c = cart.Cart()
    e = expect_error(c.remove_item, "mango")
    assert isinstance(e, KeyError)

# subtotal with bulk discount and rounding

def test_subtotal_bulk_discount_and_rounding():
    c = cart.Cart()
    # 10 items at $1 each - bulk 5% -> line_total 9.5
    c.add_item("item", 1, 10)
    assert pytest.approx(c.subtotal(), rel=1e-12) == 9.5
    # 100 items at $0.2 each - bulk 15% -> line_total 17
    c.add_item("expensive", 0.2, 100)
    expected = round((1*10)*0.95 + (0.2*100)*0.85, 2)
    assert pytest.approx(c.subtotal(), rel=1e-12) == expected

# total calculation with coupon and shipping

def test_total_with_coupon_and_shipping():
    c = cart.Cart()
    c.add_item("item", 200, 3)  # subtotal before discount: 600 - bulk 0 -> 600
    amount_before_coupons = c.subtotal()  # 600.0
    assert amount_before_coupons == 600.0
    # Apply SAVE10 coupon: 10% off = 540
    total_with_coupon = c.total(coupon="SAVE10")
    expected_amount_after_discount = cart.apply_discount(amount_before_coupons, 10)
    shipping = cart.shipping_fee(expected_amount_after_discount)  # non-member by default
    expected_total = round(expected_amount_after_discount + shipping, 2)
    assert total_with_coupon == expected_total

# empty cart costs 0 no shipping

def test_empty_cart_no_shipping():
    c = cart.Cart()
    assert c.total() == 0
    assert c.subtotal() == 0

# member half shipping

def test_member_half_shipping():
    c = cart.Cart()
    c.add_item("item", 50, 5)  # subtotal 250 - bulk 5% -> 237.5
    total_nonmember = c.total(member=False)
    total_member = c.total(member=True)
    assert total_nonmember > total_member
    # non-member shipping 60
    assert pytest.approx(total_nonmember, rel=1e-12) == round(237.5 + 60, 2)
    # member shipping half 30
    assert pytest.approx(total_member, rel=1e-12) == round(237.5 + 30, 2)
