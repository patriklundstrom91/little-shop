from django import forms
from shop.models import ProductVariant


class AddToBagForm(forms.Form):
    variant = forms.ModelChoiceField(queryset=ProductVariant.objects.none())
    quantity = forms.IntegerField(min_value=1, initial=1)

    def __init__(self, product, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['variant'].queryset = product.variants.filter(active=True)
