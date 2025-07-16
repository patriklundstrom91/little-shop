from decimal import Decimal
from django.conf import settings
from .models import BagItem
from .utils import get_bag_filter


def bag_contents(request):
    bag_items = BagItem.objects.filter(**get_bag_filter(request))

    subtotal = sum(
        item.variant.product.price * item.quantity for item in bag_items
    )
    if subtotal < settings.FREE_DELIVERY_THRESHOLD:
        delivery = subtotal * Decimal(
            settings.STANDARD_DELIVERY_PERCENTAGE / 100
        )
        free_delivery_delta = settings.FREE_DELIVERY_THRESHOLD - subtotal
    else:
        delivery = 0
        free_delivery_delta = 0
    grand_total = subtotal + delivery
    item_count = sum(item.quantity for item in bag_items)

    return {
        'bag_items': bag_items,
        'bag_subtotal': subtotal,
        'bag_delivery': delivery,
        'bag_grand_total': grand_total,
        'bag_count': item_count,
        'free_delivery_delta': free_delivery_delta
    }
