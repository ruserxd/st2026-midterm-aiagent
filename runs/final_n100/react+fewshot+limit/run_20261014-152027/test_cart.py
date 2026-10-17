import pytest
import cart

# ---------- apply_discount ---------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price", [-1, -0.01])
def test_apply_discount_price_negative(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 105])
def test_apply_discount_percent_out_of_range(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# ---------- bulk_discount_percent ---------

def test_bulk_discount_percent_brackets():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@pytest.mark.parametrize("qty", [0, -1, 2.5])
def test_bulk_discount_percent_invalid_quantity(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ---------- parse_coupon ---------

def test_parse_coupon_valid_cases():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon(" SAVE5 ") == 5

@pytest.mark.parametrize("code", ["", "SAVEX", "SAVE51", "123", "SAVE-1", "SAVETWO"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee ---------

def test_shipping_fee_basic():
    assert cart.shipping_fee(999) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0

assertion = pytest.mark.parametrize("member", [True, False])
@assertion
def test_shipping_fee_member(member):
    expected = 30 if member else 60
    assert cart.shipping_fee(200, member=member) == expected

@pytest.mark.parametrize("subtotal", [-1, -0.01])
def test_shipping_fee_negative(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---------- Cart class ---------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_initially_empty_items(self):
        assert self.cart.items() == {}

    def test_add_item_new_and_existing(self):
        self.cart.add_item("apple", 100, 2)
        assert self.cart.items() == {"apple": 2}
        # add same item with same price increases quantity
        self.cart.add_item("apple", 100, 3)
        assert self.cart.items() == {"apple": 5}

    def test_add_item_price_mismatch(self):
        self.cart.add_item("banana", 50, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 60, 2)

    @pytest.mark.parametrize("price,qty", [(-10,1), (5,-3)])
    def test_add_item_invalid(self, price, qty):
        with pytest.raises(ValueError):
            self.cart.add_item("orange", price, qty)

    def test_remove_item_partial_and_complete(self):
        self.cart.add_item("cherry", 30, 4)
        self.cart.remove_item("cherry", 2)
        assert self.cart.items() == {"cherry": 2}
        # removing more than remaining removes item
        self.cart.remove_item("cherry", 5)
        assert self.cart.items() == {}

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("pear", 1)

    def test_subtotal_simple_and_discounted(self):
        # No bulk discount yet
        self.cart.add_item("widget", 100, 9)  # subtotal 900
        assert self.cart.subtotal() == 900.0
        # Add more to trigger 5% discount on that item
        self.cart.add_item("widget", 100, 1)
        # Now quantity 10 => 5% discount: 900*0.95 = 855
        assert self.cart.subtotal() == 855.0
        # Adding another distinct item with bulk discount
        self.cart.add_item("gadget", 200, 50)  # 50 units => 10% off on that line
        # gadget subtotal: 200*50=10000 -> 90% = 9000
        # total subtotal: 855 + 9000 = 9855
        assert self.cart.subtotal() == 9855.0

    def test_total_no_coupon_member(self):
        self.cart.add_item("item", 200, 1)
        # subtotal 200 -> no discount
        # shipping fee non-member: 60
        expected = round((200 + 60), 2)
        assert self.cart.total(member=False) == expected

    def test_total_with_coupon(self):
        self.cart.add_item("item", 100, 1)
        subtotal_after_coupon = 100 * (1 - 10/100)  # coupon SAVE10
        shipping = cart.shipping_fee(subtotal_after_coupon)
        total = round(subtotal_after_coupon + shipping, 2)
        assert self.cart.total(coupon="SAVE10") == total

    def test_total_invalid_coupon_raises(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")

    def test_total_empty_cart_zero_cost(self):
        # Empty cart should cost 0, no shipping
        assert self.cart.total() == 0.0
