from django.db import models
from django.urls import reverse
from decimal import Decimal

class Category(models.Model):
    name = models.CharField(max_length=200, verbose_name="نام دسته‌بندی")
    slug = models.SlugField(max_length=200, unique=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, verbose_name="والد")
    image = models.ImageField(upload_to='category_bg/', blank=True, null=True, verbose_name="تصویر پس‌زمینه")

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('shop:product_list_by_category', args=[self.slug])

class Product(models.Model):
    PRODUCT_TYPE_NORMAL = 'normal'
    PRODUCT_TYPE_RANK = 'rank'
    PRODUCT_TYPE_KIT = 'kit'

    PRODUCT_TYPE_CHOICES = [
        (PRODUCT_TYPE_NORMAL, "محصول معمولی"),
        (PRODUCT_TYPE_RANK, "رنک"),
        (PRODUCT_TYPE_KIT, "کیت"),
    ]

    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="دسته‌بندی")
    name = models.CharField(max_length=200, verbose_name="نام محصول")
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(verbose_name="توضیحات")
    specifications = models.TextField(
        verbose_name="مشخصات کامل محصول", 
        blank=True, 
        null=True, 
        help_text="برای رنک‌ها: fly : tick -- spawner : cross -- (هر خط با -- جدا می‌شود، tick = تیک سبز، cross/zarb = ضربدر قرمز). برای سایر محصولات: متن عادی"
    )
    product_type = models.CharField(
        max_length=20,
        choices=PRODUCT_TYPE_CHOICES,
        default=PRODUCT_TYPE_NORMAL,
        verbose_name="نوع محصول",
        help_text="مشخص کنید این محصول رنک است، کیت است یا محصول معمولی",
    )
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="قیمت (تومان)", help_text="قیمت قدیمی - فقط برای نمایش استفاده می‌شود")
    wart_coin_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="قیمت (وارت کوین)",
        help_text="قیمت محصول به وارت کوین - این قیمت برای خرید استفاده می‌شود"
    )
    image = models.ImageField(upload_to='products/%Y/%m/%d', verbose_name="تصویر محصول")
    available = models.BooleanField(default=True, verbose_name="موجود")
    has_monthly_options = models.BooleanField(default=False, verbose_name="دارای گزینه‌های ماهانه", help_text="اگر فعال باشد، می‌توانید گزینه‌های ماهانه برای این محصول اضافه کنید")
    luckperms_group = models.CharField(
        max_length=64,
        blank=True,
        verbose_name="گروه LuckPerms",
        help_text="نام دقیق گروه روی سرور (مثلاً vip+). اگر خالی باشد از config/rank_mapping.json استفاده می‌شود.",
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('shop:product_detail', args=[self.slug])


class ProductMonth(models.Model):
    """
    گزینه‌های ماهانه برای محصولات (مثلاً 1 ماه، 3 ماه، 6 ماه، 12 ماه)
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='monthly_options', verbose_name="محصول")
    months = models.PositiveIntegerField(verbose_name="تعداد ماه", help_text="مثلاً 1 برای یک ماه، 3 برای سه ماه")
    original_price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="قیمت اصلی (تومان)", help_text="قیمت قدیمی - فقط برای نمایش")
    discount_price = models.DecimalField(
        max_digits=10, 
        decimal_places=0, 
        blank=True, 
        null=True, 
        verbose_name="قیمت با تخفیف (تومان)",
        help_text="قیمت قدیمی - فقط برای نمایش"
    )
    wart_coin_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="قیمت (وارت کوین)",
        help_text="قیمت این گزینه به وارت کوین"
    )
    image = models.ImageField(
        upload_to='products/months/%Y/%m/%d', 
        blank=True, 
        null=True, 
        verbose_name="عکس",
        help_text="عکس مخصوص این گزینه ماهانه (اختیاری)"
    )
    description = models.TextField(verbose_name="توضیحات کامل", help_text="توضیحات کامل این گزینه ماهانه")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش", help_text="برای مرتب‌سازی گزینه‌ها")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "گزینه ماهانه"
        verbose_name_plural = "گزینه‌های ماهانه"
        ordering = ['order', 'months']
        unique_together = ['product', 'months']  # هر محصول نمی‌تواند دو گزینه با همان تعداد ماه داشته باشد

    def __str__(self):
        return f"{self.product.name} - {self.months} ماه"
    
    def get_final_price(self):
        """قیمت نهایی (با تخفیف یا بدون تخفیف) - برای نمایش قدیمی"""
        return self.discount_price if self.discount_price else self.original_price
    
    def get_wart_coin_price(self):
        """قیمت نهایی به وارت کوین"""
        return self.wart_coin_price
    
    def has_discount(self):
        """آیا این گزینه تخفیف دارد؟"""
        return self.discount_price is not None and self.discount_price < self.original_price
    
    def get_discount_percentage(self):
        """درصد تخفیف"""
        if self.has_discount():
            discount = self.original_price - self.discount_price
            percentage = (discount / self.original_price) * 100
            return int(percentage)
        return 0


class KitItem(models.Model):
    """
    آیتم‌های هر کیت (برای محصولاتی که نوع آن‌ها کیت است)
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='kit_items',
        verbose_name="محصول (کیت)",
    )
    title = models.CharField(max_length=200, verbose_name="نام آیتم / قابلیت")
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="توضیحات",
        help_text="توضیحات کوتاه درباره این آیتم (اختیاری)",
    )
    enchantments = models.TextField(
        blank=True,
        null=True,
        verbose_name="انچنت‌ها",
        help_text="انچنت‌های این آیتم (هر انچنت در یک خط جداگانه، مثال: sharpness II)",
    )
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش")

    class Meta:
        verbose_name = "آیتم کیت"
        verbose_name_plural = "آیتم‌های کیت"
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.product.name} - {self.title}"


class SiteSettings(models.Model):
    """
    تنظیمات کلی سایت - فقط یک رکورد باید وجود داشته باشد
    """
    site_name = models.CharField(max_length=200, default="فروشگاه ماینکرفت", verbose_name="نام سایت")
    
    # رنگ‌ها و ظاهر کلی (CSS Variables)
    primary_color = models.CharField(
        max_length=20,
        default="#4CAF50",
        verbose_name="رنگ اصلی (primary)",
        help_text="مثال: #4CAF50"
    )
    secondary_color = models.CharField(
        max_length=20,
        default="#FFC107",
        verbose_name="رنگ ثانویه (secondary)",
        help_text="مثال: #FFC107"
    )
    accent_color = models.CharField(
        max_length=20,
        default="#03A9F4",
        verbose_name="رنگ تأکیدی (accent)",
        help_text="مثال: #03A9F4"
    )
    dark_bg_color = models.CharField(
        max_length=20,
        default="#121212",
        verbose_name="رنگ پس‌زمینه تیره",
        help_text="پس‌زمینه کلی سایت (body)"
    )
    card_bg_color = models.CharField(
        max_length=50,
        default="rgba(30, 30, 30, 0.85)",
        verbose_name="رنگ پس‌زمینه کارت‌ها",
        help_text="مثال: rgba(30, 30, 30, 0.85)"
    )
    server_ip = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="آی‌پی سرور",
        help_text="آی‌پی یا دامنه سرور که در صفحه اصلی نمایش می‌شود"
    )
    text_light_color = models.CharField(
        max_length=20,
        default="#E0E0E0",
        verbose_name="رنگ متن اصلی",
        help_text="مثال: #E0E0E0"
    )
    text_muted_color = models.CharField(
        max_length=20,
        default="#9E9E9E",
        verbose_name="رنگ متن کم‌رنگ",
        help_text="مثال: #9E9E9E"
    )
    background_image = models.ImageField(
        upload_to='site_settings/', 
        blank=True, 
        null=True, 
        verbose_name="عکس پس‌زمینه صفحه اصلی",
        help_text="عکس پس‌زمینه که در تمام صفحات سایت نمایش داده می‌شود"
    )
    
    # متن‌های کلی سایت
    navbar_title = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="عنوان نوار بالا (Navbar)",
        help_text="اگر خالی باشد از نام سایت استفاده می‌شود"
    )
    footer_text = models.CharField(
        max_length=300,
        default="© 2024 فروشگاه ماینکرفت - ساخته شده با ❤️ و Django",
        verbose_name="متن فوتر",
        help_text="متنی که در پایین تمام صفحات نمایش داده می‌شود"
    )
    updated = models.DateTimeField(auto_now=True, verbose_name="آخرین به‌روزرسانی")
    
    class Meta:
        verbose_name = "تنظیمات سایت"
        verbose_name_plural = "تنظیمات سایت"
    
    def __str__(self):
        return "تنظیمات سایت"
    
    def save(self, *args, **kwargs):
        # فقط یک رکورد تنظیمات می‌تواند وجود داشته باشد
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def load(cls):
        """بارگذاری تنظیمات سایت - اگر وجود نداشت، ایجاد می‌کند"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
