# orders/models.py

from decimal import Decimal
from django.db import models
from django.conf import settings
from shop.models import Product  # فرض بر این است که Product در اپلیکیشن shop تعریف شده


class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
        null=True,
        blank=True,
        verbose_name='کاربر'
    )
    rank_applied = models.BooleanField(default=False)
    rank_error = models.TextField(blank=True, null=True)
    minecraft_username = models.CharField(
        max_length=16,
        blank=True,
        null=True,
        verbose_name='نام کاربری ماینکرفت',
        help_text='نام کاربری Minecraft برای دریافت آیتم'
    )
    first_name = models.CharField(max_length=50, verbose_name="نام")
    last_name = models.CharField(max_length=50, verbose_name="نام خانوادگی")
    email = models.EmailField(verbose_name="ایمیل")
    created = models.DateTimeField(auto_now_add=True, verbose_name="زمان ایجاد")
    updated = models.DateTimeField(auto_now=True, verbose_name="زمان به‌روزرسانی")
    paid = models.BooleanField(default=False, verbose_name="پرداخت شده")
    payment_status = models.CharField(
        max_length=50,
        default='pending',
        choices=[
            ('pending', 'در انتظار پرداخت'),
            ('completed', 'پرداخت شده'),
            ('failed', 'پرداخت ناموفق'),
            ('cancelled', 'لغو شده'),
        ],
        verbose_name="وضعیت پرداخت"
    )
    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        verbose_name="شناسه تراکنش",
        help_text="شناسه منحصر به فرد برای این سفارش"
    )
    wart_coin_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='مقدار وارت کوین پرداخت شده'
    )

    class Meta:
        ordering = ('-created',)
        verbose_name = 'سفارش'
        verbose_name_plural = 'سفارشات'

    def __str__(self):
        return f'Order {self.id}'

    def get_total_cost(self):
        """قیمت کل به وارت کوین"""
        return sum(item.get_cost() for item in self.items.all())
    
    def get_total_wart_coin_cost(self):
        """قیمت کل به وارت کوین - نام مستعار"""
        return self.get_total_cost()


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE,
        verbose_name="سفارش"
    )
    product = models.ForeignKey(
        Product,
        related_name='order_items',
        on_delete=models.CASCADE,
        verbose_name="محصول"
    )
    wart_coin_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="قیمت (وارت کوین)",
        help_text="قیمت هر واحد به وارت کوین در زمان خرید"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="تعداد")
    month_option_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="شناسه گزینه ماهانه",
        help_text="اگر این آیتم از گزینه‌های ماهانه است"
    )

    class Meta:
        verbose_name = 'آیتم سفارش'
        verbose_name_plural = 'آیتم‌های سفارش'

    def __str__(self):
        return str(self.id)

    def get_cost(self):
        """هزینه کل این آیتم به وارت کوین"""
        return self.wart_coin_price * self.quantity


class RankProvisionJob(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_APPLIED = 'applied'
    STATUS_RETRY = 'retry'
    STATUS_FAILED = 'failed'
    STATUS_DEAD_LETTER = 'dead_letter'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'در انتظار'),
        (STATUS_PROCESSING, 'در حال پردازش'),
        (STATUS_APPLIED, 'اعمال شد'),
        (STATUS_RETRY, 'تلاش مجدد'),
        (STATUS_FAILED, 'ناموفق'),
        (STATUS_DEAD_LETTER, 'صف مرده'),
    ]

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='rank_jobs',
        verbose_name='سفارش',
    )
    idempotency_key = models.CharField(max_length=128, unique=True, verbose_name='کلید یکتا')
    payload = models.JSONField(default=dict, verbose_name='داده درخواست')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='وضعیت',
    )
    attempts = models.PositiveIntegerField(default=0, verbose_name='تعداد تلاش')
    next_retry_at = models.DateTimeField(null=True, blank=True, verbose_name='تلاش بعدی')
    last_error = models.TextField(blank=True, verbose_name='آخرین خطا')
    rcon_response = models.JSONField(null=True, blank=True, verbose_name='پاسخ RCON')
    created = models.DateTimeField(auto_now_add=True, verbose_name='ایجاد')
    updated = models.DateTimeField(auto_now=True, verbose_name='به‌روزرسانی')

    class Meta:
        verbose_name = 'کار اعمال رنک'
        verbose_name_plural = 'کارهای اعمال رنک'
        ordering = ('-created',)

    def __str__(self):
        return f'RankJob #{self.id} order={self.order_id} [{self.status}]'