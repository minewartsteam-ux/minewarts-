from django import forms

class PaymentForm(forms.Form):
    """فرم پرداخت با کارت بانکی"""
    card_number = forms.CharField(
        max_length=19,
        label='شماره کارت',
        widget=forms.TextInput(attrs={
            'placeholder': '1234-5678-9012-3456',
            'maxlength': '19',
            'pattern': '[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{4}',
            'class': 'form-control',
        }),
        help_text='شماره کارت را با فرمت 1234-5678-9012-3456 وارد کنید'
    )
    
    card_holder_name = forms.CharField(
        max_length=100,
        label='نام دارنده کارت',
        widget=forms.TextInput(attrs={
            'placeholder': 'نام و نام خانوادگی',
            'class': 'form-control',
        })
    )
    
    card_expiry_month = forms.ChoiceField(
        choices=[(str(i).zfill(2), str(i).zfill(2)) for i in range(1, 13)],
        label='ماه انقضا',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    card_expiry_year = forms.ChoiceField(
        choices=[(str(i), str(i)) for i in range(2024, 2040)],
        label='سال انقضا',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    card_cvv = forms.CharField(
        max_length=4,
        min_length=3,
        label='CVV2',
        widget=forms.TextInput(attrs={
            'placeholder': '123',
            'maxlength': '4',
            'pattern': '[0-9]{3,4}',
            'class': 'form-control',
            'type': 'password',
        }),
        help_text='کد امنیتی پشت کارت (3 یا 4 رقم)'
    )
    
    def clean_card_number(self):
        card_number = self.cleaned_data.get('card_number')
        # حذف خط تیره‌ها
        card_number = card_number.replace('-', '').replace(' ', '')
        # بررسی اینکه فقط عدد باشد
        if not card_number.isdigit():
            raise forms.ValidationError('شماره کارت باید فقط شامل اعداد باشد')
        # بررسی طول شماره کارت (معمولاً 16 رقم)
        if len(card_number) < 13 or len(card_number) > 19:
            raise forms.ValidationError('شماره کارت نامعتبر است')
        # بازگرداندن با فرمت
        formatted = '-'.join([card_number[i:i+4] for i in range(0, len(card_number), 4)])
        return formatted
    
    def clean_card_cvv(self):
        cvv = self.cleaned_data.get('card_cvv')
        if not cvv.isdigit():
            raise forms.ValidationError('CVV2 باید فقط شامل اعداد باشد')
        if len(cvv) < 3 or len(cvv) > 4:
            raise forms.ValidationError('CVV2 باید 3 یا 4 رقم باشد')
        return cvv


