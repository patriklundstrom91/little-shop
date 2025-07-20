from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import ProductVariant
from .utils import notify_back_in_stock


def cache_previous_stock(sender, instance, **kwargs):
    """ signal to cache old stock of instance to compare with """
    if instance.pk:
        try:
            previous = ProductVariant.objects.get(pk=instance.pk)
            instance._previous_stock = previous.stock
        except ProductVariant.DoesNotExist:
            instance._previous_stock = 0
    else:
        instance._previous_stock = 0


@receiver(post_save, sender=ProductVariant)
def send_back_in_stock_notifications(sender, instance, **kwargs):
    """ Signal to check if stock is updated and above 0 """
    if instance.stock > 0 and getattr(instance, '_previous_stock', 0) < 1:
        notify_back_in_stock(instance)
