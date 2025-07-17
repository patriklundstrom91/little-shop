from django.contrib import admin
from django.urls import path
from . import views

app_name = 'bag'

urlpatterns = [
    path('', views.view_bag, name='view_bag'),
    path('update/', views.update_bag_item, name='update_bag_item'),
]
