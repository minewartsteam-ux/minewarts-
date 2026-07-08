from django import forms

PRODUCT_QUANTITY_CHOICES = [(i, str(i)) for i in range(1, 21)]

class CartAddProductForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=20, label='تعداد', initial=1, widget=forms.NumberInput(attrs={'min': 1, 'max': 20}))
    override = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput)
    
    def clean_override(self):
        """تبدیل string 'false' به boolean False"""
        override = self.cleaned_data.get('override')
        if isinstance(override, str):
            return override.lower() in ('true', '1', 'on')
        return bool(override)