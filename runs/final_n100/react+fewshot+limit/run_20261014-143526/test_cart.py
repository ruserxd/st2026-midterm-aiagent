import pytest
from cart import Cart

@pytest.fixture
def cart():
    return Cart()

# test_remove_item uses fixture

def test_remove_item(cart):
    cart.add_item("orange",8,5)
    cart.remove_item("orange",3)
    assert cart.items()["orange"]==2
