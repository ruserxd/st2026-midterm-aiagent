import pytest
import cart

# ---- apply_discount -----------------------------------------------------

def test_apply_discount_basic():
    assert cart.apply_discount(200, 15) == 170.0

@pytest.mark.parametrize("price, percent", [(-1, 10), (100, -5), (100, 105)])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# ---- bulk_discount_percent -----------------------------------------------

def test_bulk_discount_buckets():
    # boundaries
    assert cart.bulk_discount_percent(9) == 0
    assert cart.bulk_discount_percent(10) == 5
    assert cart.bulk_discount_percent(49) == 5
    assert cart.bulk_discount_percent(50) == 10
    assert cart.bulk_discount_percent(99) == 10
    assert cart.bulk_discount_percent(100) == 15
    assert cart.bulk_discount_percent(150) == 15

@pytest.mark.parametrize("quantity", [0, -5, 3.7])
def test_bulk_discount_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(int(quantity)) if isinstance(quantity, int) else cart.bulk_discount_percent(quantity)

# ---- parse_coupon --------------------------------------------------------

def test_parse_coupon_valid():
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save20") == 20
    assert cart.parse_coupon(" SAVE30 ") == 30

@pytest.mark.parametrize("code", ["SAVEXX", "SAVE0", "SAVE51", "NOTCUPON", ""] )
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# ---- shipping_fee --------------------------------------------------------

def test_shipping_fee_nonmember():
    assert cart.shipping_fee(999) == 60
    assert cart.shipping_fee(1000) == 0
    assert cart.shipping_fee(1500) == 0

def test_shipping_fee_member():
    assert cart.shipping_fee(999, member=True) == 30
    assert cart.shipping_fee(1000, member=True) == 0

@pytest.mark.parametrize("subtotal", [-10, -1])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# ---- Cart class ----------------------------------------------------------
class TestCart:
    def setup_method(self):
        self.c = cart.Cart()

    def test_add_item_new_and_existing(self):
        self.c.add_item("apple", 2.0, 3)
        assert self.c.items() == {"apple": 3}
        # add same item with same price increases quantity
        self.c.add_item("apple", 2.0, 2)
        assert self.c.items() == {"apple": 5}

    def test_add_item_price_mismatch(self):
        self.c.add_item("banana", 1.5, 1)
        with pytest.raises(ValueError):
            self.c.add_item("banana", 2.0, 1)

    @pytest.mark.parametrize("price, qty", [( -1, 1), (1.0, 0), (1.0, -3)])
    def test_add_item_invalid(self, price, qty):
        with pytest.raises(ValueError):
            self.c.add_item("item", price, qty)

    def test_remove_item_partial_and_full(self):
        self.c.add_item("orange", 0.5, 4)
        # remove part
        self.c.remove_item("orange", 2)
        assert self.c.items() == {"orange": 2}
        # remove remaining (exact)
        self.c.remove_item("orange", 2)
        assert self.c.items() == {}

    def test_remove_nonexistent(self):
        with pytest.raises(KeyError):
            self.c.remove_item("nonexist")

    def test_items_returns_copy(self):
        self.c.add_item("x", 1.0, 2)
        d = self.c.items()
        d["y"] = 5
        assert "y" not in self.c.items()

    def test_subtotal_with_bulk_discount(self):
        # item with quantity 12 => bulk discount 5%
        self.c.add_item("pen", 1.0, 12)
        expected = 1.0 * 12 * (1 - 0.05)  # 11.4
        assert self.c.subtotal() == round(expected, 2)
        # add another item no discount
        self.c.add_item("pencil", 0.5, 3)
        expected += 0.5 * 3
        assert self.c.subtotal() == round(expected, 2)

    def test_total_without_coupon_or_member(self):
        # subtotal 200 => shipping 60 => total 260
        self.c.add_item("book", 100, 1)
        self.c.add_item("notebook", 50, 2)  # 50*2=100 no discount
        assert self.c.subtotal() == 200.0
        assert self.c.total() == round(200 + cart.shipping_fee(200), 2)

    def test_total_with_coupon_and_member(self):
        # subtotal 300, coupon 10% => after coupon 270, shipping member half fee on 270
        self.c.add_item("a", 150, 1)
        self.c.add_item("b", 150, 1)
        assert self.c.subtotal() == 300.0
        # apply coupon SAVE10
        total = self.c.total(coupon="SAVE10", member=True)
        expected_after_coupon = 300 * (1 - 0.10)  # 270
        shipping = cart.shipping_fee(expected_after_coupon, member=True)
        assert total == round(expected_after_coupon + shipping, 2)

    def test_total_empty_cart(self):
        assert self.c.total() == 0
        assert self.c.total(member=True) == 0
        with pytest.raises(ValueError):
            # coupon invalid on empty still considered? spec says coupon error; we test
            self.c.total(coupon="BAD")
