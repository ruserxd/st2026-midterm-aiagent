import cart

# Test apply_discount

def test_apply_discount():
    assert cart.apply_discount(100, 20) == 80
    assert cart.apply_discount(50, 0) == 50
    # percent can be float
    assert cart.apply_discount(200, 25.5) == 149.5

# Test bulk_discount_percent

def test_bulk_discount_percent():
    # quantity < 10 => no discount
    assert cart.bulk_discount_percent(3) == 0
    # quantity >= 10 but <20 => 5%
    assert cart.bulk_discount_percent(15) == 5
    # quantity >=20 => 10%
    assert cart.bulk_discount_percent(25) == 10

# Test parse_coupon

def test_parse_coupon():
    # valid code format
    assert cart.parse_coupon('SAVE10') is True
    # lowercase not allowed
    assert cart.parse_coupon('save10') is False
    # empty string invalid
    assert cart.parse_coupon('') is False

# Test shipping_fee

def test_shipping_fee():
    # subtotal <50 and non-member => 7.5
    assert cart.shipping_fee(30) == 7.5
    # subtotal >=50 and non-member => 0
    assert cart.shipping_fee(60) == 0
    # member discounts shipping
    assert cart.shipping_fee(30, member=True) == 4
    assert cart.shipping_fee(60, member=True) == 0

# Test Cart class

def test_cart_basic_operations():
    c = cart.Cart()
    # initially empty
    assert c.items() == []
    assert c.subtotal() == 0
    # add item
    c.add_item('apple', 1.5, quantity=2)
    assert c.items() == [{'name': 'apple', 'unit_price': 1.5, 'quantity': 2}]
    assert c.subtotal() == 3.0
    # add another item same name
    c.add_item('apple', 1.5, quantity=3)
    assert c.items()[0]['quantity'] == 5
    # remove some quantity
    c.remove_item('apple', quantity=2)
    assert c.items()[0]['quantity'] == 3
    # remove all remaining
    c.remove_item('apple', quantity=3)
    assert c.items() == []

# Test Cart total with member and coupon

def test_cart_total_with_discounts():
    c = cart.Cart()
    c.add_item('book', 20, quantity=5)  # subtotal 100
    # no discounts: member False, no coupon
    assert c.total() == 100
    # bulk discount for 5 items => 0%? actually quantity<10 so none
    # test bulk discount logic within total
    # test shipping fee when subtotal >=50
    assert cart.shipping_fee(100) == 0
    # apply coupon with code 'SAVE20'
    c.add_item('pen', 5, quantity=2)
    # subtotal now 110; with coupon should apply discount percent from parse_coupon? assume 20%
    total_with_coupon = c.total(coupon='SAVE20')
    assert isinstance(total_with_coupon, float)
    # member discount: 10% off total
    member_total = c.total(member=True)
    assert member_total == cart.apply_discount(110, 10)
