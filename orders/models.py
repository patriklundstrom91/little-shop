from django.conf import settings
from django.db import models
from shop.models import ProductVariant
from django_countries.fields import CountryField


# Create your models here.

class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL
    )
    full_name = models.CharField(max_length=100, null=False, blank=False)
    email = models.EmailField(max_length=250, null=False, blank=False)
    phone = models.CharField(max_length=20, null=False, blank=False)
    address = models.CharField(max_length=250, null=False, blank=False)
    city = models.CharField(max_length=100, null=False, blank=False)
    postal_code = models.CharField(max_length=20, null=False, blank=False)
    state_province = models.CharField(max_length=100, null=True, blank=True)
    country = CountryField(blank_label='Country *', null=False, blank=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    delivery_cost = models.DecimalField(max_digits=8, decimal_places=2,
                                        default=0, null=False)
    order_total = models.DecimalField(max_digits=10, decimal_places=2,
                                      default=0, null=False)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2,
                                      default=0, null=False)
    paid = models.BooleanField(default=False)
    delivered = models.BooleanField(default=False)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    stripe_checkout_session_id = models.CharField(max_length=255, blank=True,
                                                  null=True, unique=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f'Order #{self.id} - {self.full_name}'
    

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', null=False,
                              blank=False, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    sku = models.CharField(max_length=250, blank=True)

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = self.variant.sku
        super().save(*args, **kwargs)
        
    def total_price(self):
        return self.price * self.quantity

