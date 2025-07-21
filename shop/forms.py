from django import forms
from .models import Product, ProductVariant, Review


class ProductForm(forms.ModelForm):
    """ Form to handle products as staff """
    class Meta:
        model = Product
        fields = ['name', 'description', 'category',
                  'price', 'image', 'active']


class ProductVariantForm(forms.ModelForm):
    """ Form to handle product variant as staff """
    class Meta:
        model = ProductVariant
        fields = ['size', 'stock', 'sku', 'active']


ProductVariantFormSet = forms.inlineformset_factory(
    Product,
    ProductVariant,
    form=ProductVariantForm,
    extra=1,
    min_num=1,
    validate_min=True,
    can_delete=True
)


class ReviewForm(forms.ModelForm):
    """ Form to write reviews as shopper """
    class Meta:
        model = Review
        fields = ['review', 'rating']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'review': forms.Textarea(attrs={'class':
                                            'form-control', 'rows': 4}),
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'published': forms.CheckboxInput(),
        }
