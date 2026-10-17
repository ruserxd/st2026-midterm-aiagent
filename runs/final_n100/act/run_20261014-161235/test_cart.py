import pytest
from cart import Cart, parse_coupon, shipping_fee, apply_discount, bulk_discount_percent

# ---------- Helper functions ----------

# helper to assert roundings using spec rounding to 2 decimals

def approx_equal(a,b,rel_tol=1e-9):
    return abs(a-b) <= rel_tol

# ---------- Test parse_coupon ----------

test_valid_codes = ["SAVE10", "save20", " SAVE30 ", "Save40"]

def test_parse_coupon_valid():
    for code in test_valid_codes:
        # strip leading/trailing spaces for expected
        expected_percent=int(''.join(filter(str.isdigit,code.strip())))
        assert parse_coupon(code) == expected_percent

# invalid codes should raise ValueError
invalid_codes = ["", "SAVE0", "SAVE51", "save-10", "NOPE10", "SAVE 20"]

def test_parse_coupon_invalid():
    for code in invalid_codes:
        with pytest.raises(ValueError):
            parse_coupon(code)

# ---------- Test shipping_fee ----------

def test_shipping_fee_non_member_free_over_threshold():
    assert shipping_fee(1000) == 0
    assert shipping_fee(1200.5) == 0


def test_shipping_fee_non_member_charged_below_threshold():
    assert shipping_fee(999.99) == 60
    assert shipping_fee(500) == 60


def test_shipping_fee_member_half_of_fee():
    assert shipping_fee(500, member=True) == 30
    assert shipping_fee(0, member=True) == 30


def test_shipping_fee_negative_subtotal_raises():
    with pytest.raises(ValueError):
        shipping_fee(-1)

# ---------- Test apply_discount ----------

def test_apply_discount_basic():
    assert apply_discount(200,15)==170.0
    # check rounding behaviour
    assert apply_discount(100,33) == 67.0


def test_apply_discount_edge_percent_bounds():
    # percent 0 and 100
    assert apply_discount(123.45,0)==123.45
    assert apply_discount(123.45,100)==0.0


def test_apply_discount_invalid_price_and_percent():
    with pytest.raises(ValueError):
        apply_discount(-10,20)
    with pytest.raises(ValueError):
        apply_discount(10,-5)
    with pytest.raises(ValueError):
        apply_discount(10,101)

# ---------- Test bulk_discount_percent ----------

def test_bulk_discount_basic():
    assert bulk_discount_percent(9) == 0
    assert bulk_discount_percent(10) == 5
    assert bulk_discount_percent(49)==5
    assert bulk_discount_percent(50)==10
    assert bulk_discount_percent(99)==10
    assert bulk_discount_percent(100)==15


def test_bulk_discount_invalid():
    with pytest.raises(ValueError):
        bulk_discount_percent(0)
    with pytest.raises(ValueError):
        bulk_discount_percent(-5)

# ---------- Test Cart class behaviour ----------

def test_cart_initial_empty():
    c=Cart()
    assert c.items()==[]
    assert c.subtotal()==0
    assert c.total()==0.0


def test_add_and_remove_items():
    c=Cart()
    c.add_item("apple",1,3)
    assert len(c.items())==1
    assert c.items()[0]["quantity"]==3
    # adding same item increases quantity
    c.add_item("Apple",2)  # different unit price treated separately by implementation
    # remove one apple
    c.remove_item("apple",1)
    assert c.items()[0]["quantity"]==2
    # removing more than present should leave zero quantity and keep the entry? spec unclear; we test that it does not crash.
    c.remove_item("apple",5)
    # ensure still present but quantity adjusted appropriately (implementation may keep negative, so check no exception)


def test_cart_subtotal_and_total_without_coupons():
    c=Cart()
    c.add_item("item1",100,2)  # subtotal 200
    assert c.subtotal()==200
    assert c.total() == round(200 + shipping_fee(200),2)


def test_cart_coupon_and_member_shipping():
    c=Cart()
    c.add_item("prod",500,1)   # subtotal 500 -> shipping 60 non-member
    # apply coupon SAVE10 => 50 discount, new subtotal 450, shipping 60
    assert c.total(coupon="SAVE10") == round(450 + shipping_fee(450),2)
    # member with same coupon -> shipping half
    assert c.total(member=True,coupon="save10") == round(450 + shipping_fee(450,member=True),2)


def test_cart_invalid_coupon():
    c=Cart()
    c.add_item("p",100,1)
    with pytest.raises(ValueError):
        c.total(coupon="badcode")

# ---------- Run tests ----------
if __name__=='__main__':
    pytest.main([__file__])
