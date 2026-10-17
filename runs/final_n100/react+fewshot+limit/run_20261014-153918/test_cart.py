import pytest
import cart

# ---------- apply_discount ---------------------------------

def test_apply_discount_valid_cases():
    assert cart.apply_discount(200, 15) == 170.0
    # boundary cases
    assert cart.apply_discount(100, 0) == 100.0
    assert cart.apply_discount(50, 100) == 0.0

# invalid price / percent

def test_apply_discount_invalid_price():
    with pytest.raises(ValueError):
        cart.apply_discount(-1, 10)

def test_apply_discount_invalid_percent_low():
    with pytest.raises(ValueError):
        cart.apply_discount(50, -5)

def test_apply_discount_invalid_percent_high():
    with pytest.raises(ValueError):
        cart.apply_discount(50, 105)

# ---------- bulk_discount_percent ----------------------------

def test_bulk_discount_percent_values():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

# invalid quantity

def test_bulk_discount_percent_invalid():
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(0)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(-5)
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(1.5)  # not an integer

# ---------- parse_coupon ------------------------------------

def test_parse_coupon_valid_cases():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save25") == 25
    assert cart.parse_coupon("   SaVe50  ") == 50
    # boundaries
    assert cart.parse_coupon("SAVE1") == 1
    assert cart.parse_coupon("SAVE50") == 50

# invalid coupons

def test_parse_coupon_invalid_cases():
    with pytest.raises(ValueError):
        cart.parse_coupon("SAV10")   # missing 'E'
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE0")   # below 1
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE51")  # above 50
    with pytest.raises(ValueError):
        cart.parse_coupon("BADCODE")

# ---------- shipping_fee ------------------------------------

def test_shipping_fee_free_and_half():
    assert cart.shipping_fee(0) == 60
    assert cart.shipping_fee(999.99) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(5000) == 0
    # member discount half fee when not free
    assert cart.shipping_fee(800, member=True) == 30
    assert cart.shipping_fee(1200, member=True) == 0

# invalid subtotal

def test_shipping_fee_invalid_subtotal():
    with pytest.raises(ValueError):
        cart.shipping_fee(-5)

# ---------- Cart functionality --------------------------------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initial_state(self):
        assert self.cart.items() == {}
        assert self.cart.subtotal() == 0.0
        assert self.cart.total() == 0.0

    def test_add_item_new_and_increment(self):
        self.cart.add_item("apple", 1.00, quantity=3)
        assert self.cart.items() == {"apple": 3}
        # adding again with same price increments quantity
        self.cart.add_item("apple", 1.00, quantity=2)
        assert self.cart.items() == {"apple": 5}

    def test_add_item_invalid_price_quantity(self):
        with pytest.raises(ValueError):
            self.cart.add_item("banana", -1, quantity=1)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 0.5, quantity=0)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 0.5, quantity=-3)

    def test_add_item_price_mismatch(self):
        self.cart.add_item("orange", 2.00, quantity=1)
        with pytest.raises(ValueError):
            # attempt to add same item with different unit price
            self.cart.add_item("orange", 2.50, quantity=1)

    def test_remove_item_partial_and_full(self):
        self.cart.add_item("pear", 0.75, quantity=4)
        self.cart.remove_item("pear", quantity=2)
        assert self.cart.items() == {"pear": 2}
        # removing more than remaining removes the item
        self.cart.remove_item("pear", quantity=5)
        assert "pear" not in self.cart.items()

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexistent", 1)

    def test_subtotal_with_bulk_discount(self):
        # quantity below bulk threshold: no discount
        self.cart.add_item("widget", 10.00, quantity=5)   # 50 total
        assert self.cart.subtotal() == 50.0
        # quantity >= 10 gives 5% discount on that item
        self.cart.remove_item("widget", quantity=5)
        self.cart.add_item("widget", 10.00, quantity=12)  # base 120 -> 5% off = 114
        assert round(self.cart.subtotal(), 2) == 114.0
        # quantity >= 50 gives 10%
        self.cart.remove_item("widget", quantity=12)
        self.cart.add_item("gadget", 20.00, quantity=55)   # base 1100 -> 10% off = 990
        assert round(self.cart.subtotal(), 2) == 990.0
        # quantity >= 100 gives 15%
        self.cart.remove_item("gadget", quantity=55)
        self.cart.add_item("thingamajig", 5.00, quantity=120)  # base 600 -> 15% off = 510
        assert round(self.cart.subtotal(), 2) == 510.0

    def test_total_without_coupon_or_member(self):
        self.cart.add_item("itemA", 20.0, quantity=2)   # subtotal 40
        # shipping fee: 60 (subtotal < 1000)
        assert round(self.cart.total(), 2) == 100.0

    def test_total_with_coupon_and_member(self):
        self.cart.add_item("itemB", 50.0, quantity=3)   # subtotal 150
        # coupon SAVE10 gives 10% off -> 135
        # shipping fee: member half of 60 = 30
        assert round(self.cart.total(member=True, coupon="SAVE10"), 2) == 165.0

    def test_total_with_invalid_coupon_raises(self):
        self.cart.add_item("itemC", 10.0, quantity=1)
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")

    def test_total_empty_cart_no_shipping(self):
        # empty cart should cost nothing and not charge shipping
        assert self.cart.total() == 0.0
