import pytest
import cart

# ---------- apply_discount -------------------------------------------------

def test_apply_discount_normal():
    assert cart.apply_discount(200, 15) == 170.0
    # rounding to two decimals
    assert cart.apply_discount(123.456, 10) == round(123.456 * 0.9, 2)


def test_apply_discount_bounds_and_errors():
    with pytest.raises(ValueError):
        cart.apply_discount(-1, 20)
    with pytest.raises(ValueError):
        cart.apply_discount(100, -5)
    with pytest.raises(ValueError):
        cart.apply_discount(100, 105)

# ---------- bulk_discount_percent ------------------------------------------

def test_bulk_discount_percent():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15


def test_bulk_discount_percent_errors():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-5)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(3.14)  # not an int

# ---------- parse_coupon ----------------------------------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save5") == 5
    assert cart.parse_coupon("   SaVe50   ") == 50


def test_parse_coupon_invalid():
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVEX")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE0")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE51")
    with pytest.raises(ValueError):
        cart.parse_coupon("10SAVE")

# ---------- shipping_fee -----------------------------------------------------

def test_shipping_fee():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0

    # members pay half of the fee when not free shipping
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(999.99, member=True) == 30
    # membership does not affect free shipping
    assert cart.shipping_fee(1000, member=True) == 0


def test_shipping_fee_errors():
    with pytest.raises(ValueError):
        cart.shipping_fee(-1)

# ---------- Cart class -------------------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initial_state(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0

    def test_add_item_new_and_existing(self):
        # add new item
        self.cart.add_item("apple", 1.20, 3)
        assert self.cart.items()["apple"] == (1.20, 3)
        assert self.cart.subtotal() == 3 * 1.20
        # add same item with same price
        self.cart.add_item("apple", 1.20, 2)
        assert self.cart.items()["apple"] == (1.20, 5)
        assert self.cart.subtotal() == 5 * 1.20

    def test_add_item_invalid(self):
        with pytest.raises(ValueError):
            self.cart.add_item("banana", -0.5, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 0.5, 0)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 0.5, -3)

    def test_add_item_price_mismatch(self):
        self.cart.add_item("orange", 1.00, 2)
        with pytest.raises(ValueError):
            # same name but different price
            self.cart.add_item("orange", 1.50, 1)

    def test_remove_item_basic_and_removal(self):
        self.cart.add_item("milk", 2.00, 4)
        self.cart.remove_item("milk", 2)
        assert self.cart.items()["milk"] == (2.00, 2)
        # remove remaining quantity
        self.cart.remove_item("milk", 2)
        assert "milk" not in self.cart.items()

    def test_remove_item_errors(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent", 1)

    def test_subtotal_and_total_member_coupon(self):
        # setup cart
        self.cart.add_item("book", 30.00, 2)   # $60
        self.cart.add_item("pen", 5.00, 10)    # bulk discount applies
        # subtotal before any discounts
        assert self.cart.subtotal() == 60 + 10 * 5.00

        # total with member price (no coupon)
        total_no_coupon = self.cart.total(member=True)
        # bulk discount on pen: quantity 10 => 5% off each unit
        expected_pen_price = 5.00 * (1 - 0.05)
        expected_total = 60 + 10 * expected_pen_price
        assert round(total_no_coupon, 2) == round(expected_total, 2)

        # total with coupon "SAVE10"
        total_with_coup = self.cart.total(member=False, coupon="SAVE10")
        # first apply bulk discount on pen then overall subtotal
        expected_total_coupon = (60 + 10 * expected_pen_price) * (1 - 0.10)
        assert round(total_with_coup, 2) == round(expected_total_coupon,
                                                2)
