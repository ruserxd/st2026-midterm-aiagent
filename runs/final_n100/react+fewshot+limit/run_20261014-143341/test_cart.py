import pytest
import cart

# --- apply_discount -----------------------------------------------------
@pytest.mark.parametrize("price,percent,result", [
    (200, 15, 170.0),          # simple case
    (100, 0, 100.0),           # no discount
    (50, 100, 0.0),            # full free
])
def test_apply_discount(price, percent, result):
    assert cart.apply_discount(price, percent) == result

# boundary and error cases
@pytest.mark.parametrize("price,percent", [(-1, 10), (50, -5), (50, 105)])
def test_apply_discount_invalid_inputs(price, percent):
    with pytest.raises(ValueError):
        cart.apply_discount(price, percent)

# --- bulk_discount_percent ----------------------------------------------
@pytest.mark.parametrize("quantity,percent", [
    (1, 0), (9, 0), (10, 5), (49, 5), (50, 10), (99, 10), (100, 15), (150, 15)
])
def test_bulk_discount_percent(quantity, percent):
    assert cart.bulk_discount_percent(quantity) == percent

@pytest.mark.parametrize("quantity", [0, -1, 2.5, "ten"])
def test_bulk_discount_percent_invalid(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# --- parse_coupon --------------------------------------------------------
@pytest.mark.parametrize("code,result", [
    ("SAVE10", 10), ("save5", 5), (" SAVE20 ", 20), ("sAvE50", 50)
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "DISCOUNT10", "", "   ", "savex"] )
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# --- shipping_fee --------------------------------------------------------
@pytest.mark.parametrize("subtotal,member,result", [
    (0, False, 60), (0, True, 30),
    (999.99, False, 60), (999.99, True, 30),
    (1000, False, 0), (1500, True, 0)
])
def test_shipping_fee(subtotal, member, result):
    assert cart.shipping_fee(subtotal, member) == result

@pytest.mark.parametrize("subtotal", [-1, -10.5])
def test_shipping_fee_invalid(subtotal):
    with pytest.raises(ValueError):
        cart.shipping_fee(subtotal)

# --- Cart class ----------------------------------------------------------
class TestCart:
    def test_initial_state(self):
        c = cart.Cart()
        assert c.items() == {}
        assert c.subtotal() == 0
        assert c.total() == 0

    # add_item tests
    def test_add_new_item(self):
        c = cart.Cart()
        c.add_item("apple", 1.5, 3)
        assert c.items() == {"apple": 3}
        assert c.subtotal() == round(1.5*3,2)   # no discount

    def test_add_existing_same_price(self):
        c = cart.Cart()
        c.add_item("banana", 0.5)
        c.add_item("banana", 0.5, 4)
        assert c.items() == {"banana": 5}

    def test_add_existing_diff_price_raises(self):
        c = cart.Cart()
        c.add_item("orange", 1.0)
        with pytest.raises(ValueError):
            c.add_item("orange", 1.2)

    @pytest.mark.parametrize("unit_price,quantity", [(-1,1),(1,-2),("one",1)])
    def test_add_invalid(self, unit_price, quantity):
        c = cart.Cart()
        with pytest.raises(ValueError):
            c.add_item("pear", unit_price, quantity)

    # remove_item tests
    def test_remove_existing(self):
        c = cart.Cart()
        c.add_item("melon", 2.0, 5)
        c.remove_item("melon", 3)
        assert c.items() == {"melon": 2}

    def test_remove_all_removes_item(self):
        c = cart.Cart()
        c.add_item("kiwi", 1.0, 4)
        c.remove_item("kiwi", 4)   # spec says remove when quantity reaches 0
        assert "kiwi" not in c.items()

    def test_remove_more_than_exists(self):
        c = cart.Cart()
        c.add_item("peach", 1.5, 2)
        # Removing 3 should delete the item per spec
        c.remove_item("peach", 3)
        assert "peach" not in c.items()

    def test_remove_nonexistent_raises(self):
        c = cart.Cart()
        with pytest.raises(KeyError):
            c.remove_item("plum")

    # bulk discount in subtotal
    def test_subtotal_with_bulk_discount(self):
        c = cart.Cart()
        c.add_item("item", 10.0, 50)   # bulk % 10 -> total 500 -> discounted 450
        assert c.subtotal() == round(450.0,2)

    def test_total_without_coupon_or_member(self):
        c = cart.Cart()
        c.add_item("toy", 20.0, 1)  # subtotal 20
        assert c.total(member=False) == round(20 + 60,2)

    def test_total_with_member(self):
        c = cart.Cart()
        c.add_item("book", 15.0, 10)  # bulk 5% -> 150-7.5=142.5
        assert c.total(member=True) == round(142.5 + 30,2)

    def test_total_with_coupon(self):
        c = cart.Cart()
        c.add_item("gadget", 100.0, 1)
        # subtotal 100; coupon SAVE10 -> 90; shipping 60 -> 150
        assert c.total(coupon="SAVE10") == round(90 + 60,2)

    def test_total_shipping_after_coupon_bug(self):
        # This test expects spec: shipping on discounted amount
        c = cart.Cart()
        c.add_item("expensive", 500.0, 1)
        # subtotal 500; coupon SAVE20 -> 400; expected shipping 60 -> total 460
        expected = round(400 + 60,2)
        assert c.total(coupon="SAVE20") == expected

    def test_total_with_discounted_shipping_bug(self):
        # This will fail if implementation uses original subtotal for shipping
        c = cart.Cart()
        c.add_item("expensive", 500.0, 1)
        # coupon SAVE50 -> 250; shipping should be 60 -> 310
        expected = round(250 + 60,2)
        assert c.total(coupon="SAVE50") == expected

    def test_total_zero_shipping_for_high_subtotal(self):
        c = cart.Cart()
        c.add_item("bulk", 200.0, 6)   # subtotal 1200
        assert c.total(member=False) == round(1200 + 0,2)

    def test_total_empty_cart_returns_zero(self):
        c = cart.Cart()
        assert c.total() == 0
