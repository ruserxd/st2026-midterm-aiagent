import pytest
import cart

# -------------------------- helper expectations from spec ---------------------------------

# expected discount amounts for sample values

def test_apply_discount_basic():
    # simple percent reduction
    assert cart.apply_discount(200, 15) == 170.0
    # round to two decimals
    assert cart.apply_discount(100, 33) == 67.00
    # zero percent
    assert cart.apply_discount(50, 0) == 50.00


def test_apply_discount_errors():
    with pytest.raises(ValueError):
        cart.apply_discount(-1, 10)
    with pytest.raises(ValueError):
        cart.apply_discount(100, -5)
    with pytest.raises(ValueError):
        cart.apply_discount(100, 105)

# bulk discount percent mapping
@pytest.mark.parametrize("quantity,expected", [
    (9,0),
    (10,5),
    (49,5),
    (50,10),
    (99,10),
    (100,15),
    (150,15)
])
def test_bulk_discount_percent(quantity,expected):
    assert cart.bulk_discount_percent(quantity) == expected

@pytest.mark.parametrize("quantity", [0,-5,2.3,None])
def test_bulk_discount_errors(quantity):
    with pytest.raises(ValueError):
        cart.bulk_discount_percent(quantity)

# coupon parsing
@pytest.mark.parametrize("code,expected", [
    ("SAVE10",10),
    ("save20",20),
    (" SAVE30 ",30),
])
def test_parse_coupon_valid(code,expected):
    assert cart.parse_coupon(code) == expected

@pytest.mark.parametrize("code", [
    "SAVEXY",   # not numeric suffix
    "SAVE0",    # below 1
    "SAVE51",   # above 50
    "DISCOUNT10",
    ""
])
def test_parse_coupon_invalid(code):
    with pytest.raises(ValueError):
        cart.parse_coupon(code)

# shipping fee logic
@pytest.mark.parametrize("subtotal,expected", [
    (0,60),
    (999.99,60),
    (1000,0),
    (1500,0)
])
def test_shipping_fee_non_member(subtotal,expected):
    assert cart.shipping_fee(subtotal) == expected

@pytest.mark.parametrize("subtotal,expected", [
    (500,30),
    (999.99,30)
])
def test_shipping_fee_member(subtotal,expected):
    assert cart.shipping_fee(subtotal, member=True) == expected

# Cart basic operations

def test_cart_add_and_items():
    c = cart.Cart()
    assert c.items() == {}
    c.add_item("apple", 1.0)
    assert c.items() == {"apple":1}
    c.add_item("banana", 0.5, quantity=2)
    assert c.items() == {"apple":1, "banana":2}
    # adding same item increases quantity
    c.add_item("apple", 1.0, quantity=3)
    assert c.items() == {"apple":4, "banana":2}


def test_cart_remove_and_items():
    c = cart.Cart()
    c.add_item("cherry", 2.0, quantity=5)
    c.remove_item("cherry", quantity=3)
    assert c.items() == {"cherry":2}
    # remove more than present should reduce to zero and delete key
    c.remove_item("cherry", quantity=5)
    assert "cherry" not in c.items()

# subtotal calculation with bulk discounts

def test_cart_subtotal():
    c = cart.Cart()
    c.add_item("toy", 10.0, quantity=9)   # no discount
    assert c.subtotal() == 90.00
    c.add_item("book", 5.0, quantity=10)  # 5% discount on books
    # book subtotal before discount: 50; after 5% -> 47.5
    assert c.subtotal() == round(90 + 47.5,2)

# total calculation with coupon and shipping

def test_cart_total_no_coupon():
    c = cart.Cart()
    c.add_item("pen", 2.0, quantity=100)  # bulk discount 15% => 170.0 after discount? actually 200-15%=170
    subtotal = c.subtotal()  # should be 200 * 0.85 = 170.00
    assert subtotal == 170.00
    total = c.total()
    # no coupon, shipping based on subtotal 170 => fee 60
    assert total == round(subtotal + 60,2)


def test_cart_total_with_coupon_and_member():
    c = cart.Cart()
    c.add_item("gift", 100.0, quantity=1)
    # subtotal 100
    assert c.subtotal() == 100.00
    total = c.total(member=True, coupon="SAVE10")
    # after coupon: 90; shipping for member on 90 -> 30
    assert total == round(90 + 30,2)

# empty cart total is zero and no shipping

def test_cart_total_empty():
    c = cart.Cart()
    assert c.total() == 0.00
    assert c.subtotal() == 0.00
