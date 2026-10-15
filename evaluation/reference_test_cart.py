"""Hand-written reference suite, derived only from the docstrings (the spec).

Used for two things:
  1. Sanity-check the evaluator: on this suite it must report 4/4 bugs found
     and 0 assertion echoes.
  2. A "human baseline" row in the results table.
"""

import pytest

import cart


# ---- apply_discount ---------------------------------------------------------
def test_apply_discount_example():
    assert cart.apply_discount(200, 15) == 170.0


@pytest.mark.parametrize("percent, expected", [(0, 100.0), (100, 0.0)])
def test_apply_discount_bounds(percent, expected):
    assert cart.apply_discount(100, percent) == expected


@pytest.mark.parametrize("price, percent", [(-1, 10), (100, -1), (100, 101)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)


# ---- bulk_discount_percent ----------------------------------------------------
@pytest.mark.parametrize("qty, expected", [
    (1, 0), (9, 0), (10, 5), (49, 5), (50, 10), (99, 10), (100, 15), (500, 15),
])
def test_bulk_discount_tiers(qty, expected):
    assert cart.bulk_discount_percent(qty) == expected


@pytest.mark.parametrize("qty", [0, -3, 2.5, "10"])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)


# ---- parse_coupon -------------------------------------------------------------
@pytest.mark.parametrize("code, expected", [
    ("SAVE10", 10), ("save10", 10), ("Save5", 5), ("  SAVE50 ", 50), ("SAVE1", 1),
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected


@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "SAVE", "SAVEX", "OFF10", "", 10, None])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)


# ---- shipping_fee ---------------------------------------------------------------
@pytest.mark.parametrize("subtotal, member, expected", [
    (0, False, 60), (999.99, False, 60), (999.99, True, 30),
    (1000, False, 0), (1000, True, 0), (5000, False, 0),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected


def test_shipping_fee_negative():
    with pytest.raises(ValueError):
        cart.shipping_fee(-1)


# ---- Cart -------------------------------------------------------------------------
def test_add_merges_quantity():
    c = cart.Cart()
    c.add_item("pen", 10, 2)
    c.add_item("pen", 10, 3)
    assert c.items() == {"pen": 5}


@pytest.mark.parametrize("price, qty", [(-1, 1), (10, 0), (10, -2), (10, 1.5)])
def test_add_invalid(price, qty):
    with pytest.raises(ValueError):
        cart.Cart().add_item("pen", price, qty)


def test_add_price_mismatch():
    c = cart.Cart()
    c.add_item("pen", 10)
    with pytest.raises(ValueError):
        c.add_item("pen", 12)


def test_items_returns_copy():
    c = cart.Cart()
    c.add_item("pen", 10)
    c.items()["pen"] = 99
    assert c.items() == {"pen": 1}


def test_remove_partial():
    c = cart.Cart()
    c.add_item("pen", 10, 3)
    c.remove_item("pen", 2)
    assert c.items() == {"pen": 1}


def test_remove_last_unit_deletes_item():
    c = cart.Cart()
    c.add_item("pen", 10, 2)
    c.remove_item("pen", 2)
    assert c.items() == {}
    assert c.subtotal() == 0


def test_remove_more_than_present_deletes_item():
    c = cart.Cart()
    c.add_item("pen", 10, 2)
    c.remove_item("pen", 5)
    assert "pen" not in c.items()


def test_remove_missing():
    with pytest.raises(KeyError):
        cart.Cart().remove_item("ghost")


def test_subtotal_with_bulk_discount():
    c = cart.Cart()
    c.add_item("pen", 10, 50)      # 500 -> 10% off -> 450
    c.add_item("book", 300, 1)     # 300 -> no discount
    assert c.subtotal() == 750.0


def test_total_empty_cart():
    assert cart.Cart().total() == 0


def test_total_member_shipping():
    c = cart.Cart()
    c.add_item("book", 300, 1)
    assert c.total(member=True) == 330.0


def test_total_coupon_case_insensitive():
    c = cart.Cart()
    c.add_item("book", 300, 1)
    assert c.total(coupon="save10") == 330.0     # 270 + 60


def test_total_shipping_uses_amount_after_coupon():
    c = cart.Cart()
    c.add_item("tv", 1100, 1)
    # 1100 -> SAVE20 -> 880, which is below 1000, so shipping 60 applies.
    assert c.total(coupon="SAVE20") == 940.0


def test_total_invalid_coupon():
    c = cart.Cart()
    c.add_item("book", 300, 1)
    with pytest.raises(ValueError):
        c.total(coupon="SAVE99")
