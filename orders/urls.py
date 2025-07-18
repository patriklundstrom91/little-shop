from django.contrib import admin
from django.urls import path
from . import views
from .views import stripe_webhook

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout_view, name='checkout'),
    path('start/', views.create_checkout_session,
         name='create_checkout_session'),
    path('webhook/', stripe_webhook, name='stripe_webhook'),
    path('success/', views.checkout_success, name='checkout_success'),
    path('cancel/', views.checkout_cancel, name='checkout_cancel'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/export/csv/', views.export_orders_csv,
         name='export_orders_csv'),
]
