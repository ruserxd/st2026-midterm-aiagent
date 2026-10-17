import cart
import pytest

# helper: create cart with items

def make_cart(items):
    c = cart.Cart()
    for name, price, qty in items:
        c.add_item(name, price, qty)
    return c

# test coupon parsing valid
@pytest.mark.parametrize("code", ["SAVE10", "save20", "  SaVe30 "])
def test_parse_coupon_valid(code):
    assert cart.parse_coupon(code) == int(code.strip()[4:])

# test invalid coupons
@pytest.mark.parametrize("code", ["SAVE0", "SAVE51", "DISCOUNT10", "SAVEX"] )
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# test total without shipping when empty
def test_empty_cart_total():
    c = cart.Cart()
    assert c.total() == 0.00

# test subtotal calculation
def test_subtotal():
    c = make_cart([("item1", 10, 2), ("item2", 5, 3)])
    assert c.subtotal() == 10*2 + 5*3

# shipping fee spec not provided but we can infer: use function directly
# test total with coupon and shipping
# assume shipping_fee is based on subtotal after coupon; let's check rounding

def test_total_with_coupon_and_shipping():
    c = make_cart([("item", 100, 1)])
    # no coupon, should be 100 + shipping (unknown) but we can compute via shipping_fee function
    base = c.subtotal()
    expected_no_coupon = round(base + cart.shipping_fee(base), 2)
    assert c.total() == expected_no_coupon
    # with valid coupon reducing 10%
    percent = cart.parse_coupon("SAVE10")
    after_discount = base * (1 - percent/100.0)
    expected_with_coupon = round(after_discount + cart.shipping_fee(after_discount), 2)
    assert c.total(coupon="SAVE10") == expected_with_coupon

# test member flag does not affect shipping in spec; but we can check that passing member True doesn't change result when same coupon

def test_member_flag_ignored_in_total():
    c = make_cart([("item", 50, 1)])
    assert c.total(member=True) == c.total()

# test remove_item reduces quantity or removes item

def test_remove_item_quantity_and_removal():
    c = cart.Cart()
    c.add_item("apple", 2, 5)
    c.remove_item("apple", 3)
    assert c.items()["apple"]["quantity"] == 2
    # remove remaining
    c.remove_item("apple", 2)
    assert "apple" not in c.items()

# test adding new item updates quantity

def test_add_existing_item():
    c = cart.Cart()
    c.add_item("banana", 1, 3)
    c.add_item("banana", 1, 4)
    assert c.items()["banana"]["quantity"] == 7
