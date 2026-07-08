from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re
from .models import SupportTicket, SupportMessage, UserProfile

class CustomUserCreationForm(UserCreationForm):
    """فرم ثبت‌نام با اعتبارسنجی پیشرفته"""
    email = forms.EmailField(
        label='ایمیل',
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@email.com',
            'autocomplete': 'email'
        })
    )
    first_name = forms.CharField(
        label='نام',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'نام خود را وارد کنید',
            'autocomplete': 'given-name'
        })
    )
    last_name = forms.CharField(
        label='نام خانوادگی',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'نام خانوادگی خود را وارد کنید',
            'autocomplete': 'family-name'
        })
    )
    username = forms.CharField(
        label='نام کاربری',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'نام کاربری خود را انتخاب کنید',
            'autocomplete': 'username'
        }),
        help_text='حداقل 3 کاراکتر، فقط حروف، اعداد و _'
    )
    minecraft_username = forms.CharField(
        label='نام کاربری ماینکرفت',
        max_length=16,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'مثال: Steve123',
            'autocomplete': 'off'
        }),
        help_text='نام کاربری Minecraft شما (حداکثر 16 کاراکتر) - این فیلد اجباری است'
    )
    password1 = forms.CharField(
        label='رمز عبور',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'رمز عبور قوی انتخاب کنید',
            'autocomplete': 'new-password'
        }),
        help_text='حداقل 8 کاراکتر، شامل حروف و اعداد'
    )
    password2 = forms.CharField(
        label='تکرار رمز عبور',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'رمز عبور را دوباره وارد کنید',
            'autocomplete': 'new-password'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'minecraft_username', 'password1', 'password2')
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if len(username) < 3:
            raise ValidationError('نام کاربری باید حداقل 3 کاراکتر باشد.')
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError('نام کاربری فقط می‌تواند شامل حروف انگلیسی، اعداد و _ باشد.')
        if User.objects.filter(username=username).exists():
            raise ValidationError('این نام کاربری قبلاً استفاده شده است.')
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('این ایمیل قبلاً ثبت شده است.')
        return email
    
    def clean_minecraft_username(self):
        """اعتبارسنجی نام کاربری ماینکرفت"""
        minecraft_username = self.cleaned_data.get('minecraft_username', '').strip()
        if not minecraft_username:
            raise ValidationError('نام کاربری ماینکرفت الزامی است.')
        if len(minecraft_username) > 16:
            raise ValidationError('نام کاربری ماینکرفت نمی‌تواند بیشتر از 16 کاراکتر باشد.')
        if not re.match(r'^[a-zA-Z0-9_]{1,16}$', minecraft_username):
            raise ValidationError('نام کاربری ماینکرفت نامعتبر است. فقط از حروف انگلیسی، اعداد و _ استفاده کنید.')
        return minecraft_username
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if len(password1) < 8:
            raise ValidationError('رمز عبور باید حداقل 8 کاراکتر باشد.')
        if not re.search(r'[A-Za-z]', password1):
            raise ValidationError('رمز عبور باید شامل حداقل یک حرف باشد.')
        if not re.search(r'[0-9]', password1):
            raise ValidationError('رمز عبور باید شامل حداقل یک عدد باشد.')
        return password1
    
    def save(self, commit=True):
        """ذخیره User و ایجاد Profile"""
        user = super().save(commit=commit)
        if commit:
            # ایجاد پروفایل با نام کاربری ماینکرفت
            minecraft_username = self.cleaned_data.get('minecraft_username', '').strip()
            UserProfile.objects.create(
                user=user,
                minecraft_username=minecraft_username
            )
        return user

class CustomAuthenticationForm(AuthenticationForm):
    """فرم لاگین با استایل بهتر"""
    username = forms.CharField(
        label='نام کاربری یا ایمیل',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'نام کاربری یا ایمیل',
            'autocomplete': 'username',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label='رمز عبور',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'رمز عبور',
            'autocomplete': 'current-password'
        })
    )
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        # امکان لاگین با ایمیل یا نام کاربری
        if '@' in username:
            try:
                user = User.objects.get(email=username)
                return user.username
            except User.DoesNotExist:
                pass
        return username


class SupportTicketCreateForm(forms.ModelForm):
    """فرم ایجاد تیکت جدید"""
    subject = forms.CharField(
        label='موضوع تیکت',
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'موضوع تیکت را وارد کنید...',
        }),
        help_text='موضوع تیکت خود را به صورت خلاصه وارد کنید'
    )
    
    class Meta:
        model = SupportTicket
        fields = ['subject']
    
    def clean_subject(self):
        subject = self.cleaned_data.get('subject', '').strip()
        if not subject:
            raise ValidationError('موضوع تیکت نمی‌تواند خالی باشد.')
        if len(subject) < 3:
            raise ValidationError('موضوع تیکت باید حداقل 3 کاراکتر باشد.')
        return subject


class SupportMessageForm(forms.ModelForm):
    """فرم ارسال پیام در تیکت (چت)"""
    message = forms.CharField(
        label='متن پیام',
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'پیام خود را بنویسید...',
        }),
        help_text='پیام خود را به صورت کامل و واضح بنویسید'
    )
    
    class Meta:
        model = SupportMessage
        fields = ['message']
    
    def clean_message(self):
        message = self.cleaned_data.get('message', '').strip()
        if not message:
            raise ValidationError('متن پیام نمی‌تواند خالی باشد.')
        if len(message) < 5:
            raise ValidationError('متن پیام باید حداقل 5 کاراکتر باشد.')
        return message

