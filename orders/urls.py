from django.contrib import admin
from django.urls import path
from .views import stripe_webhook

app_name = 'orders'

urlpatterns = [
    path('webhook/', stripe_webhook, name='stripe_webhook'),
]
