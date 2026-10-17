import pytest
import cart

# apply_discount tests
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (50, 100, 0.0),
])
def test_apply_discount_valid(price, percent, result):
    assert cart.apply_discount(price, percent) == result

@pytest.mark.parametrize("price", [-10, -1, -0.01])
def test_apply_discount_negative_price_raises(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 10)

@pytest.mark.parametrize("percent", [-5, 101])
def test_apply_discount_invalid_percent_raises(percent):
    with pytest.raises(ValueError):
        cart.apply_discount(100, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize("quantity,expected", [
    (9, 0),
    (10, 5),
    (49, 5),
    (50, 10),
    (99, 10),
    (100, 15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0, -1, -5])
def test_bulk_discount_invalid_quantity_raises(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10),
    ("save20", 20),
    (" SAVE30 ", 30),
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", ["SAVEX", "save0", "save51", "INVALID", "  "])
def test_parse_coupon_invalid_raises(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal,member,expected", [
    (1000, False, 0),
    (1500, True, 0),
    (999.99, False, 60),
    (500, True, 30),
])
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize("subtotal", [-1, -100])
def test_shipping_fee_negative_subtotal_raises(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart tests
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_items(self):
        self.cart.add_item("apple", 1.0, 3)
        assert self.cart.items() == {"apple": 3}
        # Add same item increases quantity
        self.cart.add_item("apple", 1.0, 2)
        assert self.cart.items()["apple"] == 5

    def test_add_invalid_unit_price_or_quantity(self):
        with pytest.raises(ValueError):
            self.cart.add_item("banana", -1.0, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("banana", 1.0, 0)

    def test_add_same_name_different_price_raises(self):
        self.cart.add_item("orange", 2.0, 1)
        with pytest.raises(ValueError):
            self.cart.add_item("orange", 3.0, 1)

    def test_remove_item(self):
        self.cart.add_item("pear", 5.0, 4)
        self.cart.remove_item("pear", 2)
        assert self.cart.items()["pear"] == 2
        # Removing remaining quantity removes the item
        self.cart.remove_item("pear", 2)
        assert "pear" not in self.cart.items()

    def test_remove_nonexistent_raises(self):
        with pytest.raises(KeyError):
            self.cart.remove_item("nonexist")

    def test_subtotal_and_total(self):
        self.cart.add_item("item1", 10.0, 2)   # subtotal 20
        self.cart.add_item("item2", 5.0, 4)    # subtotal 20 more = 40
        assert self.cart.subtotal() == 40
        # Total without member or coupon
        assert self.cart.total() == 40 + cart.shipping_fee(40)
        # Member gets half shipping fee
        total_member = 40 + cart.shipping_fee(40, True)
        assert self.cart.total(member=True) == total_member
        # Apply coupon SAVE10: reduce by 10%
        subtotal_after_coupon = 40 * 0.9
        expected_total_coupon = subtotal_after_coupon + cart.shipping_fee(subtotal_after_coupon)
        assert self.cart.total(coupon="SAVE10") == pytest.approx(expected_total_coupon, rel=1e-12)

    def test_total_with_large_subtotal_free_shipping(self):
        # Set subtotal >=1000 to get free shipping
        self.cart.add_item("expensive", 200.0, 6)   # 1200
        assert self.cart.total() == 1200  # shipping 0
