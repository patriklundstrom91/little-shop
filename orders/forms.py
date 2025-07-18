from django import forms
from orders.models import Order


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['full_name', 'email', 'phone', 'address', 'city',
                  'postal_code', 'state_province', 'country']
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(OrderForm, self).__init__(*args, **kwargs)
        if user and user.is_authenticated:
            profile = user.userprofile
            self.fields['full_name'].initial = profile.full_name
            self.fields['email'].initial = profile.email
            self.fields['phone'].initial = profile.phone
            self.fields['address'].initial = profile.address
            self.fields['city'].initial = profile.city
            self.fields['postal_code'].initial = profile.postal_code
            self.fields['state_province'].initial = profile.state_province
            self.fields['country'].initial = profile.country
            self.fields['save_to_profile'] = forms.BooleanField(
                required=False, initial=True, label='Save to profile'
            )

