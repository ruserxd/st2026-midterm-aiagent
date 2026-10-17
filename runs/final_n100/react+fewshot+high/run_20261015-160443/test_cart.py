import pytest
import cart

# apply_discount tests
@pytest.mark.parametrize("price, percent, expected", [
    (200, 15, 170.0),
    (100, 0, 100.0),
    (100, 100, 0.0),
    (50, 50, 25.0),
    (0, 50, 0.0)
])
def test_apply_discount(price, percent, expected):
    assert cart.apply_discount(price, percent) == pytest.approx(expected)

@pytest.mark.parametrize("price, percent", [
    (-1, 10),
    (100, -5),
    (100, 105),
    (50, 200)
])
def test_apply_discount_invalid(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# bulk_discount_percent tests
@pytest.mark.parametrize("quantity, expected_percent", [
    (9, 0),
    (10,5),
    (49,5),
    (50,10),
    (99,10),
    (100,15),
    (200,15)
])
def test_bulk_discount_percent(quantity, expected_percent):
    assert cart.bulk_discount_percent(quantity) == expected_percent

@pytest.mark.parametrize("quantity", [0, -1])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# parse_coupon tests
@pytest.mark.parametrize("code, expected", [
    ("SAVE20",20),
    ("save5",5),
    ("   SaVe30  ",30)
])
def test_parse_coupon_valid(code, expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code",[ "SAKE","SAVE51","SAVE0","SAVe","20SAVE","","sa v e10"])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping_fee tests
@pytest.mark.parametrize("subtotal, member, expected_fee", [
    (999, False, 60),
    (999, True, 30),
    (1000, False, 0),
    (1500, True, 0)
])
def test_shipping_fee(subtotal, member, expected_fee):
    assert cart.shipping_fee(subtotal, member) == expected_fee

@pytest.mark.parametrize("subtotal", [-1,-10])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# Cart tests
class TestCart:
    def test_add_item_new(self):
        c = cart.Cart()
        c.add_item("apple", 1.0, 3)
        assert c.items() == {"apple": 3}

    def test_add_item_increment_same_price(self):
        c = cart.Cart()
        c.add_item("apple", 1.0, 3)
        c.add_item("apple", 1.0, 2)
        assert c.items() == {"apple":5}

    def test_add_item_different_price_error(self):
        c = cart.Cart()
        c.add_item("apple", 1.0, 3)
        with pytest.raises(ValueError):
            c.add_item("apple", 1.5, 1)

    @pytest.mark.parametrize("unit_price, quantity", [
        (-1, 2),
        (1.0, 0),
        (1.0, -3)
    ])
    def test_add_item_invalid(self, unit_price, quantity):
        c = cart.Cart()
        with pytest.raises(ValueError):
            c.add_item("apple", unit_price, quantity)

    def test_remove_item_partial_and_full(self):
        c = cart.Cart()
        c.add_item("banana", 2.0, 4)
        c.remove_item("banana", 2)
        assert c.items() == {"banana":2}
        c.remove_item("banana", 3) # remove remaining and extra
        assert "banana" not in c.items()

    def test_remove_nonexistent(self):
        c = cart.Cart()
        with pytest.raises(KeyError):
            c.remove_item("orange",1)

    def test_items_returns_copy_or_immutable(self):
        c=cart.Cart()
        c.add_item("apple",1.0,3)
        d=c.items()
        d["apple"]=10
        assert c.items() == {"apple":3}  # ensure original not mutated

    def test_subtotal_basic_and_discount(self):
        c=cart.Cart()
        c.add_item("item1",20.0,12)   # discount 5%
        c.add_item("item2",10.0,5)    # no discount
        expected = round(20.0*12*(1-0.05)+10.0*5,2)
        assert c.subtotal() == pytest.approx(expected)

    def test_subtotal_rounding(self):
        c=cart.Cart()
        c.add_item("item3",9.99,12)  # discount 5%
        expected = round(9.99*12*(1-0.05),2)
        assert c.subtotal() == pytest.approx(expected)

    def test_add_item_zero_price(self):
        c=cart.Cart()
        c.add_item("free",0.0,5)
        assert c.items() == {"free":5}

    def test_remove_item_exact(self):
        c=cart.Cart()
        c.add_item("banana",2.0,4)
        c.remove_item("banana",4)
        assert "banana" not in c.items()

    def test_total_empty_cart(self):
        c=cart.Cart()
        assert c.total() == 0.0

    def test_total_no_coupon_non_member(self):
        c=cart.Cart()
        c.add_item("item1",20.0,12)
        c.add_item("item2",10.0,5)
        subtotal = c.subtotal()
        expected = round(subtotal + cart.shipping_fee(subtotal), 2)
        assert c.total() == pytest.approx(expected)

    def test_total_no_coupon_member(self):
        c=cart.Cart()
        c.add_item("item1",20.0,12)
        c.add_item("item2",10.0,5)
        subtotal = c.subtotal()
        expected = round(subtotal + cart.shipping_fee(subtotal, member=True), 2)
        assert c.total(member=True) == pytest.approx(expected)

    def test_total_with_coupon_non_member(self):
        c=cart.Cart()
        c.add_item("item1",20.0,12)
        c.add_item("item2",10.0,5)
        subtotal = c.subtotal()
        discounted = round(subtotal * (1 - cart.parse_coupon("SAVE10") / 100), 2)
        expected = round(discounted + cart.shipping_fee(discounted), 2)
        assert c.total(coupon="SAVE10") == pytest.approx(expected)

    def test_total_with_coupon_member(self):
        c=cart.Cart()
        c.add_item("item1",20.0,12)
        c.add_item("item2",10.0,5)
        subtotal = c.subtotal()
        discounted = round(subtotal * (1 - cart.parse_coupon("SAVE10") / 100), 2)
        expected = round(discounted + cart.shipping_fee(discounted, member=True), 2)
        assert c.total(member=True, coupon="SAVE10") == pytest.approx(expected)

    def test_total_invalid_coupon(self):
        c=cart.Cart()
        with pytest.raises(ValueError):
            c.total(coupon="INVALID")
