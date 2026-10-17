import cart
import pytest

# ------------------ apply_discount ---------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0
    # rounding check
    assert cart.apply_discount(101, 50) == 50.5
    assert cart.apply_discount(100, 33) == 67.0

# percentage bounds
@pytest.mark.parametrize(
    "price,percent",
    [
        (10, -1),     # negative percent
        (10, 101),    # too high
        (-5, 50),     # negative price
        (100, 3.5),   # float percent fine
    ],
)
def test_apply_discount_invalid_args(price, percent):
    if percent < 0 or percent > 100:
        with pytest.raises(ValueError):
            cart.apply_discount(price, percent)
    else:  # only price negative should raise
        with pytest.raises(ValueError):
            cart.apply_discount(price, percent)

# ------------------ bulk_discount_percent ---------------------------------

def test_bulk_discount_levels():
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15

@pytest.mark.parametrize("qty", [0, -1, 2.5])
def test_bulk_discount_invalid(qty):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(qty)

# ------------------ parse_coupon ---------------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("10OFF") == 10

def test_parse_coupon_invalid():
    with pytest.raises(ValueError):
        cart.parse_coupon("abc123")

# ------------------ Cart behavior ---------------------------------
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_add_and_items(self):
        self.c.add_item("apple", 1.0, quantity=2)
        self.c.add_item("banana", 0.5)
        items = {i[0]: i[1] for i in self.c.items()}
        assert items == {"apple": (1.0, 2), "banana": (0.5, 1)}

    def test_subtotal(self):
        self.c.add_item("apple", 3.0, quantity=4)
        self.c.add_item("orange", 2.0, quantity=2)
        assert self.c.subtotal() == 3.0 * 4 + 2.0 * 2

    def test_remove_and_subtotal(self):
        self.c.add_item("apple", 5.0, quantity=3)
        self.c.remove_item("apple", quantity=1)
        assert self.c.items()[0][1] == (5.0, 2)  # check remaining qty
        assert self.c.subtotal() == 10.0

    def test_total_no_coupon(self):
        self.c.add_item("widget", 20.0)
        assert self.c.total(member=False) == 25.0

    def test_total_with_valid_coupon_and_shipping(self):
        self.c.add_item("gadget", 40.0)
        assert self.c.total(coupon="SAVE10") == 41.0

    def test_total_with_invalid_coupon(self):
        self.c.add_item("item", 30.0)
        with pytest.raises(ValueError):
            self.c.total(coupon="BADCODE")

    def test_empty_cart_total(self):
        assert self.c.total() == 0

# ------------------ shipping_fee behavior (through total) ---------------------------------

def test_shipping_fee_on_zero_subtotal():
    c = cart.Cart()
    assert c.total() == 0
