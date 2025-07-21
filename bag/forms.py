from django import forms
from shop.models import ProductVariant


class AddToBagForm(forms.Form):
    variant = forms.ModelChoiceField(queryset=ProductVariant.objects.none())
    quantity = forms.IntegerField(min_value=1)

    def __init__(self, *args, **kwargs):
        product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)
        if product:
            self.fields['variant'].queryset = product.variants.filter(
                active=True
            )

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        variant = self.cleaned_data.get('variant')
        if variant and quantity > variant.stock:
            raise forms.ValidationError(
                f'Only {variant.stock} items available in stock.'
            )
        return quantity
