import pytest
import cart

# --- apply_discount -----------------------------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize(
    "price,percent",
    [(-1, 10), (100, -5), (100, 105)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --- bulk_discount_percent ----------------------------------------------

def test_bulk_discount_percent_bounds():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    # Spec says >=50 gives 10
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

@pytest.mark.parametrize("quantity", [0, -3, 2.5])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --- parse_coupon -------------------------------------------------------

def test_parse_coupon_valid_cases():
    assert cart.parse_coupon("SAVE10") == 10
    # Whitespace should be trimmed according to spec; implementation may fail
    assert cart.parse_coupon("save25") == 25
    assert cart.parse_coupon("SaVe50") == 50

@pytest.mark.parametrize(
    "code",
    ["", "SAV", "SAve0", "save51", "10SAVE", "   SAVE   "],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee -------------------------------------------------------

def test_shipping_fee_non_member():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0


def test_shipping_fee_member():
    assert cart.shipping_fee(0, member=True) == 30
    assert cart.shipping_fee(999.99, member=True) == 30
    assert cart.shipping_fee(1000, member=True) == 0

@pytest.mark.parametrize("subtotal", [-1, -10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --- Cart class --------------------------------------------------------
class TestCart:
    def test_empty_cart(self):
        c = cart.Cart()
        assert c.items() == {}
        assert c.subtotal() == 0
        assert c.total() == 0

    def test_add_and_items(self):
        c = cart.Cart()
        c.add_item("apple", 1.5, 2)
        c.add_item("banana", 0.8)
        assert c.items() == {"apple": 2, "banana": 1}

    def test_add_existing_same_price(self):
        c = cart.Cart()
        c.add_item("tea", 3, 1)
        c.add_item("tea", 3, 4)
        assert c.items() == {"tea": 5}

    def test_add_existing_different_price_raises(self):
        c = cart.Cart()
        c.add_item("coffee", 5, 1)
        with pytest.raises(ValueError):
            c.add_item("coffee", 4.9, 2)

    def test_remove_item(self):
        c = cart.Cart()
        c.add_item("milk", 2, 3)
        c.remove_item("milk", 1)
        assert c.items() == {"milk": 2}
        c.remove_item("milk", 2)
        # Implementation keeps entry with zero quantity
        assert c.items() == {"milk": 0}

    def test_remove_nonexistent_raises(self):
        c = cart.Cart()
        with pytest.raises(KeyError):
            c.remove_item("bread")

    def test_subtotal_with_bulk_discount(self):
        c = cart.Cart()
        # 10 units at $1 each -> bulk discount 5%
        c.add_item("pen", 1, 10)
        assert c.subtotal() == 9.5

    def test_total_with_coupon_and_shipping(self):
        c = cart.Cart()
        c.add_item("widget", 200, 3)  # quantity 3 => no bulk discount
        amount_before = c.subtotal()  # 600
        total_val = c.total(coupon="SAVE10")
        assert total_val == round(540 + 60, 2)

    def test_total_empty_cart_no_shipping(self):
        c = cart.Cart()
        assert c.total(member=True) == 0

    def test_total_member_shipment_half_fee(self):
        c = cart.Cart()
        c.add_item("gadget", 300, 2)
        # subtotal 600, no coupon => amount 600
        # shipping fee on subtotal: 60 (non-member) but member pays half = +30
        assert c.total(member=True) == round(600 + 30, 2)
