import pytest
import cart

# ---------- apply_discount tests ----------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price,percent", [
    (100, -1),   # percent < 0
    (100, 101),  # percent > 100
])
def test_apply_discount_invalid_percent(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

@pytest.mark.parametrize("price", [-10, -1])
def test_apply_discount_negative_price(price):
    with pytest.raises(ValueError):
        cart.apply_discount(price, 20)

# ---------- bulk_discount_percent tests ----------

def test_bulk_discount_thresholds():
    assert cart.bulk_discount_percent(5) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@pytest.mark.parametrize("quantity", [0, -1, 2.5])
def test_bulk_discount_invalid_quantity(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# ---------- parse_coupon tests ----------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon("  SaVe5  ") == 5

@pytest.mark.parametrize("code", ["SAVEX", "ABC10", "SAVE0", "SAVE51", ""])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---------- shipping_fee tests ----------

def test_shipping_fee_free_and_member():
    # subtotal above free threshold
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(2000, member=True) == 0

    # subtotal below free threshold
    assert cart.shipping_fee(500) == 60
    assert cart.shipping_fee(500, member=True) == 30

@ pytest.mark.parametrize("subtotal", [-1, -10])
 def test_shipping_fee_invalid(subtotal):
     with pytest.raises(ValueError):
         cart.shipping_fee(subtotal)

# ---------- Cart tests ----------
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_and_remove_items(self):
        # Add new item
        self.cart.add_item("apple", 1.0, quantity=3)
        assert self.cart.items() == {"apple": 3}

        # Add more of same item with same unit price
        self.cart.add_item("apple", 1.0, quantity=2)
        assert self.cart.items() == {"apple": 5}

        # Adding same name with different price should raise ValueError
        with pytest.raises(ValueError):
            self.cart.add_item("apple", 1.5, quantity=1)

        # Remove some quantity
        self.cart.remove_item("apple", quantity=2)
        assert self.cart.items() == {"apple": 3}

        # Removing more than present removes item completely
        self.cart.remove_item("apple", quantity=4)
        assert self.cart.items() == {}

        # Removing non-existent item raises KeyError
        with pytest.raises(KeyError):
            self.cart.remove_item("banana")

    def test_subtotal_bulk_discount(self):
        # 10 apples, unit price 2 -> bulk discount 5%
        self.cart.add_item("apple", 2.0, quantity=10)
        assert self.cart.subtotal() == pytest.approx(19.0)  # 20*0.95

        # 50 oranges at $1 each -> 10% discount
        self.cart.add_item("orange", 1.0, quantity=50)
        expected = 19.0 + (50 * 1.0 * 0.9)  # 45
        assert self.cart.subtotal() == pytest.approx(expected)

    def test_total_with_coupon_and_shipping(self):
        # No items => total is 0
        assert self.cart.total() == 0

        # Add 10 apples (2 each) subtotal after bulk discount = $19.00
        self.cart.add_item("apple", 2.0, quantity=10)
        # Total without coupon or shipping: subtotal + shipping(60?) but shipping is only if subtotal <1000 -> yes 60
        # Coupon SAVE10 reduces subtotal by 10% => 17.1, then add shipping fee 30 (member) or 60 non-member.
        assert self.cart.total(coupon="SAVE10") == pytest.approx(47.1)
        # Member pays half shipping
        assert self.cart.total(member=True, coupon="SAVE10") == pytest.approx(17.1 + 30)
        # No coupon but member: subtotal 19 + 30 =49
        assert self.cart.total(member=True) == pytest.approx(49)

    def test_total_invalid_coupon(self):
        self.cart.add_item("apple", 2.0, quantity=10)
        with pytest.raises(ValueError):
            self.cart.total(coupon="BADCODE")
