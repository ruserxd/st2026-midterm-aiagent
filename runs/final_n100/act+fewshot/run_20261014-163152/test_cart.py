import pytest
import cart

# Helper: round to two decimals as per apply_discount spec

def rounded(value):
    return round(value + 1e-8, 2)

@pytest.mark.parametrize(
    "price, percent, expected",
    [
        (200, 15, 170.0),      # example
        (100, 0, 100.0),       # no discount
        (50, 100, 0.0),        # full discount
        (123.45, 7.89, 114.06),# decimal percent
    ],
)
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == rounded(expected)

@pytest.mark.parametrize(
    "price, percent",
    [(-10, 5), (50, -1), (50, 101)],
)
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

@pytest.mark.parametrize(
    "quantity, expected",
    [
        (5, 0),
        (10, 5),
        (49, 5),
        (50, 10),
        (99, 10),
        (100, 15),
        (150, 15),
    ],
)
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize(
    "quantity",
    [0, -5, 3.5],
)
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

@pytest.mark.parametrize(
    "code, expected",
    [
        ("SAVE10", 10),
        (" save25 ", 25),
        ("SaVe1", 1),
    ],
)
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize(
    "code",
    ["SAVEXX", "SAVE0", "SAVE51", "ABC10", "", None],
)
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

@pytest.mark.parametrize(
    "subtotal, member, expected",
    [
        (1000, False, 0),
        (1200, True, 0),
        (999.99, False, 60),
        (200, True, 30),
        (0, False, 60),
    ],
)
def test_shipping_fee(subtotal, member, expected):
    assert cart.shipping_fee(subtotal, member) == expected

@pytest.mark.parametrize(
    "subtotal",
    [-5, -100],
)
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Tests for Cart class
class TestCart:
    def setup_method(self):
        self.cart = cart.Cart()

    def test_add_item_and_items(self):
        self.cart.add_item("apple", 1.0, 3)
        self.cart.add_item("banana", 0.5)
        items = self.cart.items()
        assert len(items) == 2
        names = {item['name'] for item in items}
        assert names == {"apple", "banana"}
        # check unit_price and quantity
        apple = next(i for i in items if i['name'] == "apple")
        assert apple['unit_price'] == 1.0
        assert apple['quantity'] == 3

    def test_remove_item(self):
        self.cart.add_item("pear", 2.0, 5)
        self.cart.remove_item("pear", 2)
        items = self.cart.items()
        assert items[0]['quantity'] == 3
        # removing more than present removes the item
        self.cart.remove_item("pear", 5)
        assert not self.cart.items()

    def test_subtotal(self):
        self.cart.add_item("book", 10.0, 2)   # 20
        self.cart.add_item("pen", 1.5, 4)     # 6
        assert self.cart.subtotal() == 26.0

    def test_total_no_discounts(self):
        self.cart.add_item("widget", 50.0, 1)
        # subtotal 50 -> shipping 60, member False
        total = self.cart.total(member=False)
        assert total == 110.0

    def test_total_with_member_and_coupon(self):
        self.cart.add_item("gadget", 200.0, 3)  # subtotal 600
        # bulk discount on quantity 3 -> 0%
        # coupon SAVE10 gives 10% off on subtotal after shipping? Assume applied to subtotal
        total = self.cart.total(member=True, coupon="SAVE10")
        # shipping fee for 600: 60 (member 30), so subtotal + shipping = 630
        # apply coupon 10% -> 567.0
        assert total == 567.0

    def test_total_with_bulk_discount_and_coupon(self):
        self.cart.add_item("item", 20.0, 150)  # quantity 150 => bulk 15%
        subtotal = 20.0 * 150  # 3000
        discounted_subtotal = cart.apply_discount(subtotal, 15)
        shipping = 0  # subtotal >=1000
        total_before_coupon = discounted_subtotal + shipping
        # coupon SAVE5 -> 5% discount
        final_total = cart.apply_discount(total_before_coupon, 5)
        assert self.cart.total(coupon="SAVE5") == round(final_total,2)

    def test_total_invalid_coupon(self):
        with pytest.raises(ValueError):
            self.cart.total(coupon="INVALID")

    def test_add_nonpositive_price_or_quantity(self):
        with pytest.raises(ValueError):
            self.cart.add_item("bad", -1.0, 2)
        with pytest.raises(ValueError):
            self.cart.add_item("bad2", 1.0, 0)
