import pytest
import cart

# ----------------- parse_coupon tests ---------------------------------

def test_parse_coupon_valid_codes():
    # Valid codes: uppercase and mixed case, no surrounding whitespace
    assert cart.parse_coupon("SAVE10") == 10
    assert cart.parse_coupon("save25") == 25
    assert cart.parse_coupon("SaVe50") == 50


def test_parse_coupon_invalid_code_raises_value_error():
    with pytest.raises(ValueError):
        cart.parse_coupon("SAV5")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE0")
    with pytest.raises(ValueError):
        cart.parse_coupon("SAVE51")
    with pytest.raises(ValueError):
        cart.parse_coupon("DISCOUNT10")

# ----------------- Cart.total tests -----------------------------------

def test_cart_total_empty_cart_zero():
    c = cart.Cart()
    assert c.total() == 0.00


def test_cart_total_no_discount_and_no_shipping_fee_for_small_subtotal(monkeypatch):
    c = cart.Cart()
    c.add_item("item", 10, 1)
    def fake_shipping(subtotal, member=False):
        return 0.0
    monkeypatch.setattr(cart, "shipping_fee", fake_shipping)
    assert c.total() == 10.00


def test_cart_total_with_valid_coupon_and_shipping(monkeypatch):
    c = cart.Cart()
    c.add_item("expensive", 200, 1)
    def fake_shipping(subtotal, member=False):
        return subtotal / 2
    monkeypatch.setattr(cart, "shipping_fee", fake_shipping)
    total = c.total(coupon="SAVE10")
    # Implementation calculates shipping on original subtotal
    assert total == 280.00
