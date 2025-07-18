from django.contrib import admin
from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    path('view/', views.view_profile, name='view_profile'),
    path('edit/', views.edit_profile, name='edit_profile'),
    path('delete/', views.delete_profile, name='delete_profile'),
]
