from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import re


class UserProfile(models.Model):
    """
    پروفایل کاربر - شامل اطلاعات اضافی مانند نام کاربری ماینکرفت
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='کاربر'
    )
    minecraft_username = models.CharField(
        max_length=16,
        verbose_name='نام کاربری ماینکرفت',
        help_text='نام کاربری Minecraft شما (حداکثر 16 کاراکتر)',
        blank=False,
        null=False
    )
    created = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'پروفایل کاربر'
        verbose_name_plural = 'پروفایل‌های کاربران'

    def __str__(self):
        return f'{self.user.username} - {self.minecraft_username}'
    
    def clean(self):
        """اعتبارسنجی نام کاربری ماینکرفت"""
        if self.minecraft_username:
            username = self.minecraft_username.strip()
            if not re.match(r'^[a-zA-Z0-9_]{1,16}$', username):
                from django.core.exceptions import ValidationError
                raise ValidationError({
                    'minecraft_username': 'نام کاربری ماینکرفت نامعتبر است. فقط از حروف انگلیسی، اعداد و _ استفاده کنید (حداکثر 16 کاراکتر).'
                })


class WartCoin(models.Model):
    """
    کیف پول وارت کوین کاربر - هر کاربر یک کیف پول دارد
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wart_coin',
        verbose_name='کاربر'
    )
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='موجودی (وارت کوین)'
    )
    created = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'کیف پول وارت کوین'
        verbose_name_plural = 'کیف پول‌های وارت کوین'
        ordering = ['-updated']

    def __str__(self):
        return f'{self.user.username} - {self.balance} WC'

    def add_coins(self, amount, reason='', transaction_type='manual'):
        """افزودن وارت کوین به کیف پول"""
        if amount <= 0:
            raise ValueError('مقدار باید بیشتر از صفر باشد')
        
        amount_decimal = Decimal(str(amount))
        new_balance = Decimal(str(self.balance)) + amount_decimal
        
        self.balance = new_balance
        self.save(update_fields=['balance', 'updated'])
        self.refresh_from_db()
        
        WartCoinTransaction.objects.create(
            wallet=self,
            amount=amount_decimal,
            transaction_type=transaction_type,
            reason=reason,
            balance_after=self.balance
        )
        return self.balance

    def deduct_coins(self, amount, reason='', transaction_type='purchase'):
        """کسر وارت کوین از کیف پول"""
        if amount <= 0:
            raise ValueError('مقدار باید بیشتر از صفر باشد')
        
        amount_decimal = Decimal(str(amount))
        current_balance = Decimal(str(self.balance))
        
        if current_balance < amount_decimal:
            raise ValueError('موجودی ناکافی است')
        
        new_balance = current_balance - amount_decimal
        
        self.balance = new_balance
        self.save(update_fields=['balance', 'updated'])
        self.refresh_from_db()
        
        WartCoinTransaction.objects.create(
            wallet=self,
            amount=-amount_decimal,
            transaction_type=transaction_type,
            reason=reason,
            balance_after=self.balance
        )
        return self.balance


class BulkDiscount(models.Model):
    """
    تخفیف خرید عمده وارت کوین - هرچه بیشتر بخری، ارزان‌تر
    """
    min_amount = models.PositiveIntegerField(
        verbose_name='حداقل مقدار (وارت کوین)',
        help_text='حداقل تعداد وارت کوین برای دریافت این تخفیف'
    )
    price_per_coin = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='قیمت هر وارت کوین (تومان)',
        help_text='قیمت هر واحد وارت کوین برای این بازه'
    )
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='ترتیب',
        help_text='برای مرتب‌سازی - مقادیر کمتر اول نمایش داده می‌شوند'
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'تخفیف خرید عمده'
        verbose_name_plural = 'تخفیف‌های خرید عمده'
        ordering = ['order', 'min_amount']
        unique_together = ['min_amount']

    def __str__(self):
        return f'{self.min_amount}+ WC = {self.price_per_coin} تومان/واحد'


class WartCoinPurchase(models.Model):
    """
    خرید وارت کوین با پول واقعی
    """
    STATUS_CHOICES = [
        ('pending', 'در انتظار پرداخت'),
        ('completed', 'پرداخت شده'),
        ('failed', 'پرداخت ناموفق'),
        ('cancelled', 'لغو شده'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='coin_purchases',
        verbose_name='کاربر'
    )
    coin_amount = models.PositiveIntegerField(verbose_name='مقدار وارت کوین')
    price_per_coin = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='قیمت هر واحد (تومان)'
    )
    total_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='قیمت کل (تومان)'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='وضعیت پرداخت'
    )
    payment_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='شناسه پرداخت'
    )
    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        verbose_name='شناسه تراکنش'
    )
    created = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'خرید وارت کوین'
        verbose_name_plural = 'خریدهای وارت کوین'
        ordering = ['-created']

    def __str__(self):
        return f'{self.user.username} - {self.coin_amount} WC - {self.total_price} تومان'

    def mark_completed(self, payment_id=None):
        """علامت‌گذاری خرید به عنوان پرداخت شده و افزودن وارت کوین"""
        if self.payment_status == 'completed':
            return
        
        self.payment_status = 'completed'
        if payment_id:
            self.payment_id = payment_id
        
        wallet, created = WartCoin.objects.get_or_create(user=self.user)
        if not created:
            wallet.refresh_from_db()
        
        wallet.add_coins(
            amount=self.coin_amount,
            reason=f'خرید {self.coin_amount} وارت کوین',
            transaction_type='purchase'
        )
        wallet.refresh_from_db()
        self.save(update_fields=['payment_status', 'payment_id', 'updated'])


class WartCoinTransaction(models.Model):
    """
    تمام تراکنش‌های وارت کوین - برای لاگ و گزارش
    """
    TRANSACTION_TYPES = [
        ('purchase', 'خرید'),
        ('spend', 'خرج'),
        ('manual', 'دستی (ادمین)'),
        ('refund', 'بازپرداخت'),
    ]

    wallet = models.ForeignKey(
        WartCoin,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='کیف پول'
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='مقدار',
        help_text='مقدار مثبت برای افزودن، منفی برای کسر'
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES,
        verbose_name='نوع تراکنش'
    )
    reason = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='دلیل'
    )
    balance_after = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='موجودی بعد از تراکنش'
    )
    related_order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='coin_transactions',
        verbose_name='سفارش مرتبط'
    )
    created = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ تراکنش')

    class Meta:
        verbose_name = 'تراکنش وارت کوین'
        verbose_name_plural = 'تراکنش‌های وارت کوین'
        ordering = ['-created']

    def __str__(self):
        sign = '+' if self.amount >= 0 else ''
        return f'{self.wallet.user.username} - {sign}{self.amount} WC - {self.get_transaction_type_display()}'


class WartCoinSettings(models.Model):
    """
    تنظیمات وارت کوین - قیمت پایه وارت کوین
    """
    base_price_per_coin = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('1000.00'),
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='قیمت پایه هر وارت کوین (تومان)',
        help_text='قیمت پایه هر واحد وارت کوین - اگر تخفیف عمده تنظیم نشده باشد، از این قیمت استفاده می‌شود'
    )
    updated = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'تنظیمات وارت کوین'
        verbose_name_plural = 'تنظیمات وارت کوین'

    def __str__(self):
        return f'قیمت پایه: {self.base_price_per_coin} تومان/وارت کوین'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
    
    def get_price_for_amount(self, amount):
        from django.db.models import Q
        discount = BulkDiscount.objects.filter(
            min_amount__lte=amount,
            is_active=True
        ).order_by('-min_amount').first()
        
        if discount:
            return discount.price_per_coin * Decimal(str(amount))
        return self.base_price_per_coin * Decimal(str(amount))


class SiteInfo(models.Model):
    """
    اطلاعات سایت (بخش More Info) - قابل ویرایش از پنل ادمین
    """
    discord_invite_link = models.URLField(
        blank=True,
        null=True,
        verbose_name='لینک دعوت دیسکورد',
        help_text='لینک دعوت سرور دیسکورد'
    )
    minecraft_server_ip = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='آی‌پی سرور ماینکرفت',
        help_text='آی‌پی یا دامنه سرور ماینکرفت'
    )
    admin_info_text = models.TextField(
        blank=True,
        null=True,
        verbose_name='اطلاعات ادمین‌ها',
        help_text='اطلاعات ادمین‌های سرور (متن HTML مجاز است)'
    )
    additional_info = models.TextField(
        blank=True,
        null=True,
        verbose_name='اطلاعات اضافی',
        help_text='هرگونه اطلاعات اضافی برای نمایش در صفحه More Info (HTML مجاز است)'
    )
    updated = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'اطلاعات سایت'
        verbose_name_plural = 'اطلاعات سایت'

    def __str__(self):
        return 'اطلاعات سایت (More Info)'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


# ==================== Multi-Currency System ====================

class Currency(models.Model):
    CURRENCY_TYPES = [
        ('galion', 'Galion (طلا)'),
        ('sickle', 'Sickle (نقره)'),
        ('knut', 'Knut (برنز)'),
    ]
    
    code = models.CharField(
        max_length=20,
        unique=True,
        choices=CURRENCY_TYPES,
        verbose_name='کد ارز',
        help_text='کد واحد پولی'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='نام',
        help_text='نام کامل واحد پولی'
    )
    symbol = models.CharField(
        max_length=10,
        verbose_name='نماد',
        help_text='نماد نمایشی (مثلاً G برای Galion)'
    )
    price_per_unit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='قیمت هر واحد (تومان)',
        help_text='قیمت هر واحد این ارز به تومان'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال',
        help_text='آیا این ارز فعال است؟'
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='ترتیب نمایش',
        help_text='برای مرتب‌سازی در لیست‌ها'
    )
    created = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'ارز'
        verbose_name_plural = 'ارزها'
        ordering = ['order', 'code']

    def __str__(self):
        return f'{self.name} ({self.symbol})'

    @classmethod
    def get_galion(cls):
        return cls.objects.get_or_create(
            code='galion',
            defaults={
                'name': 'Galion',
                'symbol': 'G',
                'price_per_unit': Decimal('1000.00'),
                'order': 1
            }
        )[0]

    @classmethod
    def get_sickle(cls):
        return cls.objects.get_or_create(
            code='sickle',
            defaults={
                'name': 'Sickle',
                'symbol': 'S',
                'price_per_unit': Decimal('58.82'),
                'order': 2
            }
        )[0]

    @classmethod
    def get_knut(cls):
        return cls.objects.get_or_create(
            code='knut',
            defaults={
                'name': 'Knut',
                'symbol': 'K',
                'price_per_unit': Decimal('2.03'),
                'order': 3
            }
        )[0]


class CurrencyWallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='currency_wallet',
        verbose_name='کاربر'
    )
    galion_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='موجودی Galion'
    )
    sickle_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='موجودی Sickle'
    )
    knut_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='موجودی Knut'
    )
    created = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'کیف پول چند ارزی'
        verbose_name_plural = 'کیف پول‌های چند ارزی'
        ordering = ['-updated']

    def __str__(self):
        return f'{self.user.username} - G:{self.galion_balance} S:{self.sickle_balance} K:{self.knut_balance}'

    def get_balance(self, currency_code):
        if currency_code == 'galion':
            return self.galion_balance
        elif currency_code == 'sickle':
            return self.sickle_balance
        elif currency_code == 'knut':
            return self.knut_balance
        return Decimal('0.00')

    def add_currency(self, currency_code, amount, reason='', transaction_type='manual'):
        if amount <= 0:
            raise ValueError('مقدار باید بیشتر از صفر باشد')
        
        amount_decimal = Decimal(str(amount))
        
        if currency_code == 'galion':
            self.galion_balance += amount_decimal
        elif currency_code == 'sickle':
            self.sickle_balance += amount_decimal
        elif currency_code == 'knut':
            self.knut_balance += amount_decimal
        else:
            raise ValueError(f'ارز نامعتبر: {currency_code}')
        
        self.save(update_fields=[f'{currency_code}_balance', 'updated'])
        self.refresh_from_db()
        
        CurrencyTransaction.objects.create(
            wallet=self,
            currency_code=currency_code,
            amount=amount_decimal,
            transaction_type=transaction_type,
            reason=reason,
            balance_after=self.get_balance(currency_code)
        )
        
        return self.get_balance(currency_code)

    def deduct_currency(self, currency_code, amount, reason='', transaction_type='purchase'):
        if amount <= 0:
            raise ValueError('مقدار باید بیشتر از صفر باشد')
        
        amount_decimal = Decimal(str(amount))
        current_balance = self.get_balance(currency_code)
        
        if current_balance < amount_decimal:
            raise ValueError(f'موجودی {currency_code} ناکافی است')
        
        if currency_code == 'galion':
            self.galion_balance -= amount_decimal
        elif currency_code == 'sickle':
            self.sickle_balance -= amount_decimal
        elif currency_code == 'knut':
            self.knut_balance -= amount_decimal
        else:
            raise ValueError(f'ارز نامعتبر: {currency_code}')
        
        self.save(update_fields=[f'{currency_code}_balance', 'updated'])
        self.refresh_from_db()
        
        CurrencyTransaction.objects.create(
            wallet=self,
            currency_code=currency_code,
            amount=-amount_decimal,
            transaction_type=transaction_type,
            reason=reason,
            balance_after=self.get_balance(currency_code)
        )
        
        return self.get_balance(currency_code)

    def get_total_value_in_toman(self):
        from .models import CurrencySettings
        settings = CurrencySettings.load()
        
        galion_value = self.galion_balance * settings.get_currency_price('galion')
        sickle_value = self.sickle_balance * settings.get_currency_price('sickle')
        knut_value = self.knut_balance * settings.get_currency_price('knut')
        
        return galion_value + sickle_value + knut_value


class CurrencyTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('purchase', 'خرید'),
        ('spend', 'خرج'),
        ('manual', 'دستی (ادمین)'),
        ('refund', 'بازپرداخت'),
        ('conversion', 'تبدیل ارز'),
    ]

    wallet = models.ForeignKey(
        CurrencyWallet,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='کیف پول'
    )
    currency_code = models.CharField(
        max_length=20,
        choices=Currency.CURRENCY_TYPES,
        verbose_name='نوع ارز'
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='مقدار',
        help_text='مقدار مثبت برای افزودن، منفی برای کسر'
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES,
        verbose_name='نوع تراکنش'
    )
    reason = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='دلیل'
    )
    balance_after = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='موجودی بعد از تراکنش'
    )
    related_order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='currency_transactions',
        verbose_name='سفارش مرتبط'
    )
    conversion = models.ForeignKey(
        'CurrencyConversion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name='تبدیل ارز مرتبط'
    )
    created = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ تراکنش')

    class Meta:
        verbose_name = 'تراکنش ارزی'
        verbose_name_plural = 'تراکنش‌های ارزی'
        ordering = ['-created']

    def __str__(self):
        sign = '+' if self.amount >= 0 else ''
        currency = Currency.objects.filter(code=self.currency_code).first()
        symbol = currency.symbol if currency else self.currency_code.upper()[0]
        return f'{self.wallet.user.username} - {sign}{self.amount} {symbol} - {self.get_transaction_type_display()}'


class CurrencyConversion(models.Model):
    wallet = models.ForeignKey(
        CurrencyWallet,
        on_delete=models.CASCADE,
        related_name='conversions',
        verbose_name='کیف پول'
    )
    from_currency = models.CharField(
        max_length=20,
        choices=Currency.CURRENCY_TYPES,
        verbose_name='از ارز'
    )
    to_currency = models.CharField(
        max_length=20,
        choices=Currency.CURRENCY_TYPES,
        verbose_name='به ارز'
    )
    from_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='مقدار مبدا'
    )
    to_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='مقدار مقصد'
    )
    fee_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='کارمزد'
    )
    exchange_rate = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        verbose_name='نرخ تبدیل'
    )
    fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='درصد کارمزد'
    )
    created = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ تبدیل')

    class Meta:
        verbose_name = 'تبدیل ارز'
        verbose_name_plural = 'تبدیل‌های ارز'
        ordering = ['-created']

    def __str__(self):
        from_curr = Currency.objects.filter(code=self.from_currency).first()
        to_curr = Currency.objects.filter(code=self.to_currency).first()
        from_sym = from_curr.symbol if from_curr else self.from_currency.upper()[0]
        to_sym = to_curr.symbol if to_curr else self.to_currency.upper()[0]
        return f'{self.wallet.user.username} - {self.from_amount} {from_sym} → {self.to_amount} {to_sym}'


class CurrencySettings(models.Model):
    galion_to_sickle_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('17.00'),
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='نرخ تبدیل Galion به Sickle',
        help_text='1 Galion = ? Sickle'
    )
    sickle_to_knut_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('29.00'),
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='نرخ تبدیل Sickle به Knut',
        help_text='1 Sickle = ? Knut'
    )
    
    conversion_fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('2.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        verbose_name='کارمزد تبدیل (درصد)',
        help_text='درصد کارمزد برای تبدیل ارز (مثلاً 2.00 برای 2%)'
    )
    
    galion_price_toman = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('1000.00'),
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='قیمت Galion (تومان)'
    )
    sickle_price_toman = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('58.82'),
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='قیمت Sickle (تومان)',
        help_text='به صورت خودکار از قیمت Galion محاسبه می‌شود'
    )
    knut_price_toman = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('2.03'),
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='قیمت Knut (تومان)',
        help_text='به صورت خودکار از قیمت Galion محاسبه می‌شود'
    )
    
    updated = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'تنظیمات ارزی'
        verbose_name_plural = 'تنظیمات ارزی'

    def __str__(self):
        return f'تنظیمات ارزی - کارمزد: {self.conversion_fee_percentage}%'

    def save(self, *args, **kwargs):
        self.pk = 1
        
        if self.galion_price_toman:
            self.sickle_price_toman = self.galion_price_toman / self.galion_to_sickle_rate
            self.knut_price_toman = self.galion_price_toman / (self.galion_to_sickle_rate * self.sickle_to_knut_rate)
        
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def get_currency_price(self, currency_code):
        if currency_code == 'galion':
            return self.galion_price_toman
        elif currency_code == 'sickle':
            return self.sickle_price_toman
        elif currency_code == 'knut':
            return self.knut_price_toman
        return Decimal('0.00')

    def get_conversion_rate(self, from_currency, to_currency):
        if from_currency == to_currency:
            return Decimal('1.00')
        
        if from_currency == 'galion' and to_currency == 'sickle':
            return self.galion_to_sickle_rate
        elif from_currency == 'sickle' and to_currency == 'knut':
            return self.sickle_to_knut_rate
        
        if from_currency == 'sickle' and to_currency == 'galion':
            return Decimal('1.00') / self.galion_to_sickle_rate
        elif from_currency == 'knut' and to_currency == 'sickle':
            return Decimal('1.00') / self.sickle_to_knut_rate
        
        if from_currency == 'galion' and to_currency == 'knut':
            return self.galion_to_sickle_rate * self.sickle_to_knut_rate
        elif from_currency == 'knut' and to_currency == 'galion':
            return Decimal('1.00') / (self.galion_to_sickle_rate * self.sickle_to_knut_rate)
        
        return Decimal('1.00')

    def convert_currency(self, from_currency, to_currency, amount):
        if from_currency == to_currency:
            return amount, Decimal('0.00')
        
        rate = self.get_conversion_rate(from_currency, to_currency)
        base_amount = amount * rate
        
        fee_amount = base_amount * (self.conversion_fee_percentage / Decimal('100.00'))
        converted_amount = base_amount - fee_amount
        
        return converted_amount, fee_amount


class CurrencyPurchase(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار پرداخت'),
        ('completed', 'پرداخت شده'),
        ('failed', 'پرداخت ناموفق'),
        ('cancelled', 'لغو شده'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='currency_purchases',
        verbose_name='کاربر'
    )
    currency_code = models.CharField(
        max_length=20,
        choices=Currency.CURRENCY_TYPES,
        verbose_name='نوع ارز'
    )
    currency_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='مقدار ارز'
    )
    price_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='قیمت هر واحد (تومان)'
    )
    total_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='قیمت کل (تومان)'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='وضعیت پرداخت'
    )
    payment_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='شناسه پرداخت'
    )
    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        verbose_name='شناسه تراکنش'
    )
    created = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'خرید ارز'
        verbose_name_plural = 'خریدهای ارز'
        ordering = ['-created']

    def __str__(self):
        currency = Currency.objects.filter(code=self.currency_code).first()
        symbol = currency.symbol if currency else self.currency_code.upper()[0]
        return f'{self.user.username} - {self.currency_amount} {symbol} - {self.total_price} تومان'

    def mark_completed(self, payment_id=None):
        if self.payment_status == 'completed':
            return
        
        self.payment_status = 'completed'
        if payment_id:
            self.payment_id = payment_id
        
        wallet, created = CurrencyWallet.objects.get_or_create(user=self.user)
        if not created:
            wallet.refresh_from_db()
        
        wallet.add_currency(
            currency_code=self.currency_code,
            amount=self.currency_amount,
            reason=f'خرید {self.currency_amount} {self.currency_code}',
            transaction_type='purchase'
        )
        
        wallet.refresh_from_db()
        self.save(update_fields=['payment_status', 'payment_id', 'updated'])


# ==================== Support Ticket System (Updated) ====================

class SupportTicket(models.Model):
    """
    تیکت پشتیبانی با وضعیت‌های ساده و هوشمند
    """
    STATUS_CHOICES = (
        ('new', '🆕 جدید'),
        ('pending_user', '⏳ منتظر پاسخ کاربر'),
        ('pending_admin', '⏳ منتظر پاسخ ادمین'),
        ('answered', '✅ پاسخ داده شده'),
        ('closed', '🔒 بسته شده'),
        ('reopened', '🔓 دوباره باز شده'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='support_tickets',
        verbose_name='کاربر'
    )
    subject = models.CharField(
        max_length=255,
        verbose_name='موضوع'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name='وضعیت'
    )
    assigned_admins = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='assigned_tickets',
        blank=True,
        verbose_name='ادمین‌های اختصاص‌یافته',
        help_text='کاربرانی که می‌توانند به این تیکت پاسخ دهند'
    )
    created = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'تیکت پشتیبانی'
        verbose_name_plural = 'تیکت‌های پشتیبانی'
        ordering = ['-updated']

    def __str__(self):
        return f'تیکت #{self.id} - {self.subject}'

    def get_status_display_full(self):
        status_map = dict(self.STATUS_CHOICES)
        return status_map.get(self.status, self.status)

    def is_closed(self):
        return self.status == 'closed'

    def can_user_reply(self):
        return self.status not in ['closed']

    def can_admin_reply(self):
        return self.status not in ['closed']

    def reopen(self):
        if self.status == 'closed':
            self.status = 'reopened'
            self.save(update_fields=['status', 'updated'])
            return True
        return False

    def close(self):
        if self.status != 'closed':
            self.status = 'closed'
            self.save(update_fields=['status', 'updated'])
            return True
        return False

    def get_last_message(self):
        """دریافت آخرین پیام تیکت"""
        return self.messages.order_by('-created').first()

    def get_last_message_sender_type(self):
        """نوع فرستنده آخرین پیام: 'staff' یا 'user'"""
        last_msg = self.get_last_message()
        if last_msg:
            return 'staff' if last_msg.is_staff else 'user'
        return None

    def update_status_based_on_last_message(self):
        """به‌روزرسانی وضعیت بر اساس آخرین پیام"""
        if self.status == 'closed':
            return
        
        last_sender = self.get_last_message_sender_type()
        
        if last_sender == 'staff':
            self.status = 'pending_user'
        elif last_sender == 'user':
            self.status = 'pending_admin'
        else:
            if self.status == 'new':
                pass  # همینطور بماند
        
        self.save(update_fields=['status', 'updated'])


class SupportMessage(models.Model):
    """
    پیام‌های داخل هر تیکت (ظاهر چت)
    """
    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='تیکت'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='support_messages',
        verbose_name='فرستنده'
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name='پیام از طرف پشتیبانی'
    )
    message = models.TextField(verbose_name='متن پیام')
    created = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ارسال')

    class Meta:
        ordering = ['created']
        verbose_name = 'پیام تیکت'
        verbose_name_plural = 'پیام‌های تیکت'

    def __str__(self):
        return f'پیام در تیکت #{self.ticket_id}'