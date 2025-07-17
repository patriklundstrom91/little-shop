from django.contrib import admin
from .models import Order, OrderItem

# Register your models here.

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'full_name',
        'email',
        'city',
        'country',
        'created',
        'grand_total'
    ]
    list_filter = ['created', 'updated', 'country', 'grand_total']
    search_fields = ('full_name', 'email')
    inlines = [OrderItemInline]
    ordering = ['-created']


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'variant', 'quantity', 'price')
    search_fields = ('order__id', 'variant')