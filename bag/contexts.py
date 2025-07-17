from decimal import Decimal, ROUND_HALF_UP, getcontext
from django.conf import settings
from .models import BagItem
from .utils import get_bag_filter


getcontext().prec = 10


def to_2_decimals(val):
    return Decimal(val).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def bag_contents(request):
    bag_items = BagItem.objects.filter(**get_bag_filter(request))

    subtotal = to_2_decimals(sum(
        item.variant.product.price * item.quantity for item in bag_items
    ))
    if subtotal < settings.FREE_DELIVERY_THRESHOLD:
        delivery = to_2_decimals(subtotal * Decimal(
            settings.STANDARD_DELIVERY_PERCENTAGE / 100
        ))
        free_delivery_delta = to_2_decimals(
            settings.FREE_DELIVERY_THRESHOLD - subtotal
        )
    else:
        delivery = Decimal('0.00')
        free_delivery_delta = Decimal('0.00')
    grand_total = to_2_decimals(subtotal + delivery)
    item_count = sum(item.quantity for item in bag_items)

    return {
        'bag_items': bag_items,
        'bag_subtotal': subtotal,
        'bag_delivery': delivery,
        'bag_grand_total': grand_total,
        'bag_count': item_count,
        'free_delivery_delta': free_delivery_delta
    }
