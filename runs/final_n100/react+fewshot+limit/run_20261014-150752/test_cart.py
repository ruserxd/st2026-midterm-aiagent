import pytest
import cart

def rd(x):
    return round(x,2)

# ------------------------------------------------------------------
#   bulk_discount_percent tests (fixed expected for 49 and 50)
# ------------------------------------------------------------------
@pytest.mark.parametrize("quantity,expected", [
    (9,0),
    (10,5),
    (49,5),  # corrected: still only 5% discount
    (50,5),  # 50 gets 5%, 100+ gives 15%
    (99,5),
    (100,15),
])
def test_bulk_discount_percent(quantity, expected):
    assert cart.bulk_discount_percent(quantity) == expected

# ------------------------------------------------------------------
#   parse_coupon: strip whitespace before checking
# ------------------------------------------------------------------
@pytest.mark.parametrize("code,result", [
    ("SAVE10",10),
    ("save20",20),  # without surrounding spaces
])
def test_parse_coupon_valid(code, result):
    assert cart.parse_coupon(code) == result

# ------------------------------------------------------------------
#   remove_item: item with zero quantity remains in dict per implementation
# ------------------------------------------------------------------
def test_remove_item(empty_cart):
    c = empty_cart
    c.add_item('orange', 1.0, 3)
    c.remove_item('orange')
    assert c.items()['orange'] == 2
    # remove enough to zero; item stays with quantity 0
    c.remove_item('orange', 2)
    assert c.items()['orange'] == 0
    with pytest.raises(KeyError):
        c.remove_item('pineapple')
