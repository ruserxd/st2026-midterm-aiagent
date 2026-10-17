import cart
import pytest

# ----------- initialization and empty state ------------

def test_empty_cart_initialization():
    c = cart.Cart()
    assert isinstance(c, cart.Cart)
    assert c.items() == {}
    assert c.subtotal() == 0
    assert c.total() == 0

# ----------- adding items --------------------------------

def test_add_single_item_and_quantity_increments():
    c = cart.Cart()
    c.add_item("apple", 1.00, quantity=2)
    assert c.items() == {"apple": 2}
    # add more of same item with same price
    c.add_item("apple", 1.00, quantity=3)
    assert c.items()["apple"] == 5

# test adding new item different name

def test_add_multiple_distinct_items():
    c = cart.Cart()
    c.add_item("banana", 0.50)
    c.add_item("cherry", 2.00, quantity=4)
    assert set(c.items().keys()) == {"banana", "cherry"}

# ----------- validation of parameters -----------------

def test_add_invalid_unit_price_or_quantity():
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.add_item("pear", -0.99, quantity=1)
    with pytest.raises(ValueError):
        c.add_item("pear", 0.99, quantity=0)
    with pytest.raises(ValueError):
        c.add_item("pear", 0.99, quantity=-2)

# duplicate item but different price

def test_add_duplicate_different_price():
    c = cart.Cart()
    c.add_item("orange", 1.00)
    with pytest.raises(ValueError):
        c.add_item("orange", 1.50, quantity=1)

# ----------- removing items -----------------------------

def test_remove_existing_item_quantity_decrease_and_removal():
    c = cart.Cart()
    c.add_item("mango", 2.00, quantity=5)
    # remove less than existing
    c.remove_item("mango", quantity=3)
    assert c.items()["mango"] == 2
    # remove remaining to zero: item removed
    c.remove_item("mango", quantity=2)
    assert "mango" not in c.items()

# removing non-existent item raises KeyError

def test_remove_nonexistent_item_raises_key_error():
    c = cart.Cart()
    with pytest.raises(KeyError):
        c.remove_item("kiwi")

# ----------- subtotal calculations ----------------------

def test_subtotal_rounding_and_discount_application(monkeypatch):
    # Monkeypatch helpers to control discount behavior.
    # Assume bulk_discount_percent returns 0 for qty <=3 and 10% otherwise.
    def fake_bulk_discount(qty):
        return 10 if qty > 3 else 0
    monkeypatch.setattr(cart, "bulk_discount_percent", fake_bulk_discount)
    # apply_discount simply subtracts percentage: round to 2 decimals
    def fake_apply(price, percent):
        return price * (1 - percent/100)
    monkeypatch.setattr(cart, "apply_discount", fake_apply)

    c = cart.Cart()
    c.add_item("strawberry", 0.20, quantity=5)  # total before discount: 1.00
    expected = fake_apply(1.00, fake_bulk_discount(5))
    assert c.subtotal() == round(expected, 2)

# ----------- total calculations with coupon and shipping ---------

def test_total_with_coupon_and_shipping(monkeypatch):
    # Mock parse_coupon to return 10 for code "SAVE10"
    def fake_parse(coupon):
        if coupon == "SAVE10":
            return 10
        raise ValueError("invalid")
    monkeypatch.setattr(cart, "parse_coupon", fake_parse)
    # shipping_fee: free over 50 else $5
    def fake_shipping(subtotal, member):
        return 0 if member and subtotal >= 50 else (0 if member else 5)
    monkeypatch.setattr(cart, "shipping_fee", fake_shipping)

    c = cart.Cart()
    c.add_item("toy", 10.00, quantity=2)  # subtotal 20.00
    total_without_coupon = round(20.00 + fake_shipping(20.00, member=False), 2)
    assert c.total() == total_without_coupon

    total_with_coupon = round((20.00 - 0.10*20.00) + fake_shipping(20.00, member=False), 2)
    assert c.total(coupon="SAVE10") == total_with_coupon

# ----------- member shipping benefit -----------------

def test_member_shipping_behavior(monkeypatch):
    # Assume free shipping if subtotal >= 50 for members
    def fake_shipping(subtotal, member):
        return 0 if member and subtotal >= 50 else (5 if not member else 0)
    monkeypatch.setattr(cart, "shipping_fee", fake_shipping)
    c = cart.Cart()
    c.add_item("book", 15.00)  # subtotal 15 < 50
    assert c.total(member=True) == 15.00
    # Now add more to exceed threshold
    c.add_item("pen", 40.00)
    assert c.total(member=True) == 55.00  # free shipping applied

# ----------- invalid coupon raises ValueError -----------------

def test_invalid_coupon_raises_value_error(monkeypatch):
    def fake_parse(coupon):
        raise ValueError("invalid")
    monkeypatch.setattr(cart, "parse_coupon", fake_parse)
    c = cart.Cart()
    with pytest.raises(ValueError):
        c.total(coupon="BADCODE")

# ----------- empty cart total is zero ---------------------

def test_empty_cart_total_zero():
    c = cart.Cart()
    assert c.total() == 0
