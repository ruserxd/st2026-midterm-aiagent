import cart
import pytest

# helper function to compare with rounding

def round2(x):
    return round(float(x), 2)

class TestApplyDiscount:
    def test_valid_discount(self):
        assert cart.apply_discount(200, 15) == 170.0
        assert cart.apply_discount(100, 10) == 90.0
        assert cart.apply_discount(0, 0) == 0.0
        assert cart.apply_discount(123.45, 5) == round2(123.45 * 0.95)
    def test_invalid_price(self):
        with pytest.raises(ValueError):
            cart.apply_discount(-1, 10)
    def test_invalid_percent(self):
        with pytest.raises(ValueError):
            cart.apply_discount(100, -5)
        with pytest.raises(ValueError):
            cart.apply_discount(100, 105)

class TestBulkDiscountPercent:
    @pytest.mark.parametrize("quantity,expected", [
        (99, 10), (50, 10), (49, 5), (10,5), (9,0), (100,15), (200,15)
    ])
    def test_values(self, quantity, expected):
        assert cart.bulk_discount_percent(quantity) == expected
    def test_invalid_quantity(self):
        for q in [0, -1, 2.5]:
            with pytest.raises(ValueError):
                cart.bulk_discount_percent(q)

class TestParseCoupon:
    @pytest.mark.parametrize("code,expected", [
        ("SAVE10",10), ("save20",20), (" SAVE30 ",30),
        ("SaVe5",5)
    ])
    def test_valid(self, code, expected):
        assert cart.parse_coupon(code) == expected
    @pytest.mark.parametrize("code", [
        "SAVEX", "1234", "save0", "save51", "", "  ","SAVE-5"
    ])
    def test_invalid(self, code):
        with pytest.raises(ValueError):
            cart.parse_coupon(code)

class TestShippingFee:
    @pytest.mark.parametrize("subtotal,member,expected", [
        (1000, False, 0), (1500, True, 0),
        (999.99, False, 60), (500, True, 30),
        (0, False, 60)
    ])
    def test_cases(self, subtotal, member, expected):
        assert cart.shipping_fee(subtotal, member) == expected
    @pytest.mark.parametrize("subtotal", [-1, -10])
    def test_negative_subtotal(self, subtotal):
        with pytest.raises(ValueError):
            cart.shipping_fee(subtotal)

class TestCart:
    def test_empty_cart_total(self):
        c = cart.Cart()
        assert c.total() == 0
    def test_add_and_items(self):
        c = cart.Cart()
        c.add_item("apple", 1.5, 3)
        c.add_item("banana", 2.0)
        assert c.items() == {"apple":3, "banana":1}
        assert round(c.subtotal(),2) == round(1.5*3 + 2.0,2)
    def test_remove_item(self):
        c = cart.Cart()
        c.add_item("apple", 1.0, 5)
        c.remove_item("apple", 2)
        assert c.items() == {"apple":3}
        # removing more than present removes the item
        c.remove_item("apple", 5)
        assert c.items() == {}
    def test_total_no_coupon(self):
        c = cart.Cart()
        c.add_item("item", 100, 2)  # subtotal 200
        # member False: shipping 60 -> total 260
        assert c.total(member=False) == 260.0
        # member True: shipping 30 -> total 230
        assert c.total(member=True) == 230.0
    def test_total_with_coupon(self):
        c = cart.Cart()
        c.add_item("item", 200, 1)
        # subtotal 200, coupon SAVE10 => discount 20, amount 180, shipping 60 -> total 240
        assert c.total(coupon="SAVE10") == 240.0
    def test_total_rounding(self):
        c = cart.Cart()
        c.add_item("expensive", 333.33)
        # subtotal 333.33, no coupon, shipping 60 -> 393.33 rounded to 2 decimals
        assert c.total() == round(333.33 + 60, 2)
