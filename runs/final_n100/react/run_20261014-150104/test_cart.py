import pytest
from cart import (
    apply_discount,
    bulk_discount_percent,
    parse_coupon,
    shipping_fee,
    Cart,
)

# ---------- apply_discount tests ----------

def test_apply_discount_normal():
    assert apply_discount(200, 15) == 170.0
    assert apply_discount(100, 0) == 100.0
    assert apply_discount(50, 100) == 0.0

@pytest.mark.parametrize(
    "price",
    [-1, -10],
)
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        apply_discount(price, 10)

@pytest.mark.parametrize(
    "percent",
    [-5, 101, 150],
)
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        apply_discount(100, percent)

# ---------- bulk_discount_percent tests ----------

def test_bulk_discount_percent_brackets():
    assert bulk_discount_percent(5) == 0
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49) == 5
    assert bulk_discount_percent(50) == 10
    assert bulk_discount_percent(99) == 10
    assert bulk_discount_percent(100) == 15
    assert bulk_discount_percent(150) == 15

@pytest.mark.parametrize(
    "quantity",
    [0, -1, -20],
)
def test_bulk_discount_percent_nonpositive_raises(quantity):
    with pytest.raises(ValueError):
        bulk_discount_percent(quantity)

# ---------- parse_coupon tests ----------

def test_parse_coupon_valid():
    assert parse_coupon("SAVE10") == 10
    assert parse_coupon(" save25 ") == 25
    assert parse_coupon("SaVe1") == 1

@pytest.mark.parametrize(
    "code",
    ["SAVEX", "save0", "save51", "", "12345", "SAVE-5", "SAVETWENTY"],
)
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        parse_coupon(code)

# ---------- shipping_fee tests ----------

def test_shipping_fee_regular_and_member():
    # subtotal >= 1000: free
    assert shipping_fee(1000) == 0
    assert shipping_fee(1500.5) == 0
    # regular non-member
    assert shipping_fee(500) == 60
    # member gets half
    assert shipping_fee(200, member=True) == 30

@pytest.mark.parametrize(
    "subtotal",
    [-10, -1],
)
def test_shipping_fee_negative_raises(subtotal):
    with pytest.raises(ValueError):
        shipping_fee(subtotal)

# ---------- Cart tests ----------

def create_simple_cart():
    c = Cart()
    c.add_item("itemA", 100, quantity=2)  # subtotal: 200
    return c

def test_cart_subtotal_and_items():
    c = create_simple_cart()
    assert c.subtotal() == 200
    items = c.items()
    assert len(items) == 1
    assert items[0]["name"] == "itemA"
    assert items[0]["unit_price"] == 100
    assert items[0]["quantity"] == 2

# total without coupon or member

def test_cart_total_no_coupon_or_member():
    c = create_simple_cart()
    # subtotal=200, no coupon => 200, shipping fee 60 (non-member)
    assert c.total() == 260.0

# total with coupon discount

def test_cart_total_with_coupon():
    c = create_simple_cart()
    # coupon SAVE10 -> 10% off subtotal 200 => 180; shipping 60 => 240
    assert c.total(coupon="SAVE10") == 240.0

# total with member shipping half

def test_cart_total_member_shipping_half():
    c = create_simple_cart()
    # member, no coupon: 200 + 30 = 230
    assert c.total(member=True) == 230.0

# cart empty -> cost 0 (no shipping)

def test_empty_cart_total_zero():
    c = Cart()
    assert c.total() == 0

# coupon applied before shipping fee calculation

def test_coupon_applied_before_shipping():
    # subtotal 200, apply 50% coupon -> 100, shipping 60 => 160
    c = Cart()
    c.add_item("expensive", 200)
    assert c.total(coupon="SAVE50") == 160.0

# test invalid coupon raises ValueError in total

def test_total_invalid_coupon_raises():
    c = create_simple_cart()
    with pytest.raises(ValueError):
        c.total(coupon="invalid")

# test remove_item reduces quantity or removes item

def test_remove_item_behavior():
    c = Cart()
    c.add_item("towel", 30, quantity=3)
    # remove one
    c.remove_item("towel", quantity=1)
    assert c.items()[0]["quantity"] == 2
    # remove remaining two
    c.remove_item("towel", quantity=2)
    assert len(c.items()) == 0
    assert c.subtotal() == 0

# test bulk discount percent used by cart logic? not directly, but ensure it works

def test_bulk_discount_percent_integration_with_apply_discount():
    # buying 120 units: bulk discount 15%
    assert bulk_discount_percent(120) == 15
    # verify apply_discount with that percent
    discounted = apply_discount(200, bulk_discount_percent(120))
    assert discounted == 170.0

# test add_item default quantity is 1

def test_add_item_default_quantity():
    c = Cart()
    c.add_item("pen", 5)
    assert c.items()[0]["quantity"] == 1

# test shipping_fee rounding? (not needed as fee is integer). Done.
