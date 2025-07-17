from django import forms
from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['subject', 'review', 'rating', 'published']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'review': forms.Textarea(attrs={'class':
                                            'form-control', 'rows': 4}),
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'published': forms.CheckboxInput(),
        }
