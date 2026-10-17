import pytest
from cart import apply_discount, bulk_discount_percent, parse_coupon, shipping_fee, Cart

# ---------- apply_discount tests ----------

def test_apply_discount_valid():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(50, 100) == 0.0

@ pytest.mark.parametrize("price", [-1, -10])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        apply_discount(price, 20)

@ pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_invalid_percent(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- bulk_discount_percent tests ----------

def test_bulk_discount_brackets():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

def test_bulk_discount_invalid():
    with pytest.raises(ValueError):
        bulk_discount_percent(0)
    with pytest.raises(ValueError):
        bulk_discount_percent(-10)

# ---------- parse_coupon tests ----------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon("save20") == 20
    assert parse_coupon("  SaVe5  ") == 5

@ pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "SAVEX", "ABC10", "SAVE-10"]) 
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee tests ----------

def test_shipping_fee_standard():
    assert shipping_fee(500) == 60
    assert shipping_fee(999.99) == 60

def test_shipping_fee_member_half():
    assert shipping_fee(500, member=True) == 30

def test_shipping_fee_free_when_above_threshold():
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500) == 0

@ pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart tests ----------

def test_cart_add_and_remove():
    c = Cart()
    assert c.items() == {}
    c.add_item("apple", 100, quantity=2)
    assert c.items()["apple"] == (100, 2)
    c.remove_item("apple")
    assert c.items()["apple"] == (100, 1)
    c.remove_item("apple")
    assert "apple" not in c.items()


def test_cart_subtotal_and_total_no_discounts():
    c = Cart()
    c.add_item("a", 200, quantity=2)   # 400
    c.add_item("b", 300)               # 300
    assert c.subtotal() == 700
    assert c.total() == 700 + shipping_fee(700)


def test_cart_total_with_bulk_and_coupon_member():
    c = Cart()
    # 120 units of item X at $50 each
    c.add_item("x", 50, quantity=120)   # subtotal 6000
    # bulk discount: quantity>=100 =>15%
    expected_subtotal = 6000
    discounted_subtotal = apply_discount(expected_subtotal, 15)
    assert discounted_subtotal == 5100.0
    # member shipping half of 60 = 30
    shipping = shipping_fee(discounted_subtotal, member=True)  # free? since >=1000 => free
    assert shipping == 0
    # coupon SAVE10 (10%)
    total = discounted_subtotal + shipping - apply_discount(discounted_subtotal + shipping, 10)
    # easier compute: subtotal after bulk then apply coupon
    final_total = apply_discount(discounted_subtotal, 10) + shipping
    assert c.total(member=True, coupon="SAVE10") == pytest.approx(final_total)


def test_cart_invalid_coupon():
    c = Cart()
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# Test that Cart.total respects member flag for shipping only when subtotal after bulk discount > 0

def test_cart_member_shipping_half_when_subtotal_below_threshold():
    c = Cart()
    c.add_item("item", 100, quantity=5)  # 500
    assert c.subtotal() == 500
    total_non_member = c.total(member=False)
    total_member = c.total(member=True)
    # non-member shipping: 60, member: 30
    assert total_non_member == pytest.approx(500 + 60)
    assert total_member == pytest.approx(500 + 30)
