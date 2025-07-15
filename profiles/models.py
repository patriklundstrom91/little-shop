from django.contrib.auth.models import User
from django.db import models
from django_countries.fields import CountryField

# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=250, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True)
    state_province = models.CharField(max_length=100, blank=True, null=True)
    country = CountryField(blank_label='Country', blank=True, null=True)

    def __str__(self):
        return self.user.username
