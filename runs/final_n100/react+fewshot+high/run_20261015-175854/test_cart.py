import pytest
import cart

# ---------- apply_discount -----------------------------------------------------

def test_apply_discount_basic():
    # Simple discount, round to 2 decimals.
    assert cart.apply_discount(200.0, 15) == 170.0
    assert cart.apply_discount(100.75, 10) == round(100.75 * 0.90, 2)

def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        cart.apply_discount(-1, 20)

def test_apply_discount_percent_bounds():
    with pytest.raises(ValueError):
        cart.apply_discount(100, -5)
    with pytest.raises(ValueError):
        cart.apply_discount(100, 105)

# ---------- bulk_discount_percent ----------------------------------------------

def test_bulk_discount_percent_thresholds():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

def test_bulk_discount_invalid_quantity():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-5)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(3.2)  # not integer

# ---------- parse_coupon --------------------------------------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon('SAVE10') == 10
    assert cart.parse_coupon(' save25 ') == 25
    assert cart.parse_coupon('SaVe1') == 1
    assert cart.parse_coupon('SAVe50') == 50

def test_parse_coupon_invalid():
    with pytest.raises(ValueError):
        cart.parse_coupon('SAVE0')   # N < 1
    with pytest.raises(ValueError):
        cart.parse_coupon('SAVE51')  # N > 50
    with pytest.raises(ValueError):
        cart.parse_coupon('DISCOUNT10')
    with pytest.raises(ValueError):
        cart.parse_coupon(123)       # not a string

# ---------- shipping_fee --------------------------------------------------------

def test_shipping_fee_free_and_reduced():
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000)   == 0
    assert cart.shipping_fee(1500)   == 0

def test_shipping_fee_member_half():
    assert cart.shipping_fee(500, member=True) == 30
    assert cart.shipping_fee(1200, member=True) == 0

def test_shipping_fee_invalid_subtotal():
    with pytest.raises(ValueError):
        cart.shipping_fee(-5)

# ---------- Cart class ----------------------------------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_empty_cart_initial_state(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0
        assert self.cart.total() == 0

    # add_item -------------------------------------------------------------
    def test_add_new_item_and_quantity(self):
        self.cart.add_item('apple', 2.50, quantity=3)
        assert self.cart.items() == {'apple': 3}

    def test_add_existing_item_same_price_increases_quantity(self):
        self.cart.add_item('banana', 1.20, quantity=2)
        self.cart.add_item('banana', 1.20, quantity=4)
        assert self.cart.items() == {'banana': 6}

    def test_add_existing_item_different_price_raises(self):
        self.cart.add_item('pear', 3.00)
        with pytest.raises(ValueError):
            # price differs from existing one
            self.cart.add_item('pear', 2.50)

    def test_add_invalid_parameters(self):
        with pytest.raises(ValueError):
            self.cart.add_item('orange', -1)
        with pytest.raises(ValueError):
            self.cart.add_item('orange', 1, quantity=0)
        with pytest.raises(ValueError):
            self.cart.add_item('orange', 1, quantity=-3)

    # remove_item ------------------------------------------------------------
    def test_remove_some_quantity(self):
        self.cart.add_item('widget', 5.00, quantity=5)
        self.cart.remove_item('widget', quantity=2)
        assert self.cart.items() == {'widget': 3}

    def test_remove_entire_quantity_removes_item(self):
        self.cart.add_item('gadget', 9.99, quantity=4)
        self.cart.remove_item('gadget', quantity=4)
        assert 'gadget' not in self.cart.items()

    def test_remove_more_than_present_does_not_error_but_removes(self):
        # Removing more than present should simply remove the item.
        self.cart.add_item('tool', 12.50, quantity=1)
        self.cart.remove_item('tool', quantity=10)
        assert 'tool' not in self.cart.items()

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item('nonexistent')

    # subtotal ---------------------------------------------------------------
    def test_subtotal_with_bulk_discount_and_rounding(self):
        # 10 items of $1 each -> bulk discount 5% => unit price becomes 0.95
        self.cart.add_item('pen', 1.00, quantity=10)
        expected = round(1.00 * 10 * (1 - 0.05), 2)  # 9.50
        assert self.cart.subtotal() == expected

    def test_subtotal_empty_cart(self):
        assert self.cart.subtotal() == 0

    # total ---------------------------------------------------------------
    def test_total_without_coupon_or_member(self):
        self.cart.add_item('book', 30.00)
        subtotal = 30.00
        shipping = cart.shipping_fee(subtotal)  # subtotal < 1000 => 60
        expected_total = round(subtotal + shipping, 2)
        assert self.cart.total() == expected_total

    def test_total_with_coupon(self):
        self.cart.add_item('gift', 200.00)
        # subtotal: 200; apply coupon 20% => 160
        subtotal_after_coupon = cart.apply_discount(200, 20)  # 160.0
        shipping = cart.shipping_fee(subtotal_after_coupon)   # <1000 => 60
        expected_total = round(subtotal_after_coupon + shipping, 2)
        assert self.cart.total(coupon='SAVE20') == expected_total

    def test_total_with_invalid_coupon_raises(self):
        self.cart.add_item('ticket', 50.00)
        with pytest.raises(ValueError):
            self.cart.total(coupon='BADCODE')

    def test_total_member_receives_reduced_shipping(self):
        self.cart.add_item('game', 70.00)
        subtotal = 70.00
        shipping_nonmember = cart.shipping_fee(subtotal)      # 60
        shipping_member = cart.shipping_fee(subtotal, member=True)  # 30
        expected_total_nonmember = round(subtotal + shipping_nonmember, 2)
        expected_total_member   = round(subtotal + shipping_member,   2)
        assert self.cart.total(member=False) == expected_total_nonmember
        assert self.cart.total(member=True)  == expected_total_member

    def test_total_empty_cart_no_shipping(self):
        assert self.cart.total() == 0

# ---------- End of test_cart.py ---------------------------------------------
