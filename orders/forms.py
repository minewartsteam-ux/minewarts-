from django import forms
from .models import Order

class OrderCreateForm(forms.ModelForm):
    """فرم ایجاد سفارش - نام کاربری ماینکرفت از پروفایل کاربر گرفته می‌شود"""
    
    class Meta:
        model = Order
        fields = ['first_name', 'last_name']
        labels = {
            'first_name': 'نام',
            'last_name': 'نام خانوادگی',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }