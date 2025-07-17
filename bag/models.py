from django.conf import settings
from django.db import models
from shop.models import ProductVariant

# Create your models here.


class BagItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                             blank=True, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=50, null=True, blank=True)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    class Meta:
        unique_together = ('user', 'session_key', 'variant')


