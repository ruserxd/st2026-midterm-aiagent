"""cart -- pricing rules for a small online shop.

All money values are in New Taiwan dollars (TWD). Unless a docstring says
otherwise, results are rounded with round(x, 2).
"""

SHIPPING_BASE = 60
FREE_SHIPPING_THRESHOLD = 1000


def apply_discount(price, percent):
    """Return `price` reduced by `percent` percent, rounded to 2 decimals.

    - price must be >= 0, otherwise raise ValueError.
    - percent must satisfy 0 <= percent <= 100, otherwise raise ValueError.

    Example: apply_discount(200, 15) == 170.0
    """
    if price < 0:
        raise ValueError("price must be non-negative")
    if percent < 0 or percent > 100:
        raise ValueError("percent must be between 0 and 100")
    return round(price * (100 - percent) / 100, 2)


def bulk_discount_percent(quantity):
    """Return the bulk discount percent for buying `quantity` units of one item.

        quantity >= 100  -> 15
        quantity >= 50   -> 10
        quantity >= 10   -> 5
        otherwise        -> 0

    quantity must be a positive integer, otherwise raise ValueError.
    """
    if not isinstance(quantity, int) or quantity <= 0:
        raise ValueError("quantity must be a positive integer")
    if quantity >= 100:
        return 15
    if quantity > 50:
        return 10
    if quantity >= 10:
        return 5
    return 0


def parse_coupon(code):
    """Parse a coupon code and return its discount percent.

    A valid code is "SAVE" followed by an integer N with 1 <= N <= 50,
    for example "SAVE10". Matching is case-insensitive ("save10" is valid)
    and surrounding whitespace is ignored (" SAVE10 " is valid).
    Anything else raises ValueError.
    """
    if not isinstance(code, str):
        raise ValueError("coupon must be a string")
    text = code.strip()
    if not text.startswith("SAVE"):
        raise ValueError(f"invalid coupon: {code!r}")
    digits = text[4:]
    if not digits.isdigit():
        raise ValueError(f"invalid coupon: {code!r}")
    percent = int(digits)
    if percent < 1 or percent > 50:
        raise ValueError(f"coupon percent out of range: {percent}")
    return percent


def shipping_fee(subtotal, member=False):
    """Return the shipping fee for an order with the given item subtotal.

    - If subtotal >= 1000 shipping is free (fee 0).
    - Otherwise the fee is 60; members pay half of it (30).

    subtotal must be >= 0, otherwise raise ValueError.
    """
    if subtotal < 0:
        raise ValueError("subtotal must be non-negative")
    if subtotal >= FREE_SHIPPING_THRESHOLD:
        return 0
    fee = SHIPPING_BASE
    if member:
        fee = fee / 2
    return fee


class Cart:
    """A shopping cart holding items as name -> (unit_price, quantity)."""

    def __init__(self):
        self._lines = {}

    def add_item(self, name, unit_price, quantity=1):
        """Add `quantity` units of an item.

        Adding an item that is already in the cart increases its quantity;
        the unit price must equal the existing one, otherwise raise ValueError.
        unit_price must be >= 0 and quantity must be a positive integer,
        otherwise raise ValueError.
        """
        if unit_price < 0:
            raise ValueError("unit_price must be non-negative")
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("quantity must be a positive integer")
        if name in self._lines:
            if self._lines[name][0] != unit_price:
                raise ValueError("unit price does not match existing item")
            self._lines[name][1] += quantity
        else:
            self._lines[name] = [unit_price, quantity]

    def remove_item(self, name, quantity=1):
        """Remove `quantity` units of an item.

        When the remaining quantity reaches 0 (or less) the item is removed
        from the cart entirely. Removing an item that is not in the cart
        raises KeyError.
        """
        if name not in self._lines:
            raise KeyError(name)
        line = self._lines[name]
        line[1] -= quantity
        if line[1] < 0:
            del self._lines[name]

    def items(self):
        """Return a new dict {name: quantity} of the items in the cart."""
        return {name: line[1] for name, line in self._lines.items()}

    def subtotal(self):
        """Return the item subtotal.

        For each item: unit_price * quantity, reduced by the bulk discount
        for that item's quantity (see bulk_discount_percent). The sum is
        rounded to 2 decimals. An empty cart has subtotal 0.
        """
        total = 0
        for unit_price, quantity in self._lines.values():
            line_total = unit_price * quantity
            total += apply_discount(line_total, bulk_discount_percent(quantity))
        return round(total, 2)

    def total(self, member=False, coupon=None):
        """Return the amount the customer pays.

        1. Start from subtotal().
        2. If a coupon code is given, reduce that amount by the coupon's
           percent (see parse_coupon); an invalid coupon raises ValueError.
        3. Add shipping_fee() computed on the amount from step 2, i.e. the
           subtotal AFTER the coupon.

        The result is rounded to 2 decimals. An empty cart costs 0
        (no shipping is charged).
        """
        if not self._lines:
            return 0
        amount = self.subtotal()
        if coupon is not None:
            amount = apply_discount(amount, parse_coupon(coupon))
        return round(amount + shipping_fee(self.subtotal(), member), 2)
