from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.forms import ModelForm
from django.urls import reverse
from .models import Product, Category, SiteSettings, ProductMonth, KitItem


# ================================================================
# Category Admin
# ================================================================
class CategoryAdminForm(ModelForm):
    class Meta:
        model = Category
        fields = '__all__'
        widgets = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['parent'].queryset = Category.objects.exclude(
                pk=self.instance.pk
            ).filter(parent=None)
        else:
            self.fields['parent'].queryset = Category.objects.filter(parent=None)
        self.fields['parent'].help_text = (
            'برای ایجاد زیرمجموعه، یک دسته‌بندی اصلی را انتخاب کنید. '
            'برای دسته‌بندی اصلی، خالی بگذارید.'
        )
        self.fields['name'].help_text = 'نام دسته‌بندی را وارد کنید'
        self.fields['slug'].help_text = 'این فیلد به صورت خودکار از نام ایجاد می‌شود'
        self.fields['image'].help_text = 'تصویر پس‌زمینه برای این دسته‌بندی (اختیاری)'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryAdminForm
    list_display = [
        'name', 'parent_display', 'image_thumbnail',
        'products_count', 'view_products_link'
    ]
    list_filter = ['parent']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    list_per_page = 20
    ordering = ['name']
    readonly_fields = ['image_preview']

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'slug', 'parent'),
            'description': (
                '💡 برای ایجاد زیرمجموعه، یک دسته‌بندی اصلی را به عنوان والد انتخاب کنید. '
                'برای دسته اصلی، فیلد parent را خالی بگذارید.'
            )
        }),
        ('تصویر', {
            'fields': ('image', 'image_preview'),
            'classes': ('collapse',),
        }),
    )

    def parent_display(self, obj):
        if obj.parent:
            return format_html(
                '<span style="color: #4CAF50; font-weight: bold;">📁 {}</span>',
                obj.parent.name
            )
        return mark_safe(
            '<span style="color: #FFC107; font-weight: bold;">⭐ اصلی</span>'
        )
    parent_display.short_description = 'والد'

    def products_count(self, obj):
        count = obj.product_set.count()
        color = '#4CAF50' if count > 0 else '#999'
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; '
            'border-radius: 15px; font-weight: bold;">{} محصول</span>',
            color, count
        )
    products_count.short_description = 'تعداد محصولات'

    def image_thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" '
                'style="border-radius: 5px; object-fit: cover;" />',
                obj.image.url
            )
        return mark_safe('<span style="color: #9E9E9E;">بدون تصویر</span>')
    image_thumbnail.short_description = 'تصویر'

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="300" '
                'style="border-radius: 10px; margin-top: 10px;" />',
                obj.image.url
            )
        return mark_safe('<span style="color: #9E9E9E;">بدون تصویر</span>')
    image_preview.short_description = 'پیش‌نمایش تصویر'

    def view_products_link(self, obj):
        if obj.pk:
            return format_html(
                '<a href="/admin/shop/product/?category__id__exact={}" '
                'class="button" style="background: #2196F3; color: white; '
                'padding: 5px 15px; border-radius: 5px; text-decoration: none; '
                'margin-left: 5px;">مشاهده محصولات</a>',
                obj.id
            )
        return mark_safe('<span style="color: #999;">—</span>')
    view_products_link.short_description = 'عملیات'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent')


# ================================================================
# KitItem Inline
# ================================================================
class KitItemInline(admin.TabularInline):
    model = KitItem
    extra = 3
    fields = ['title', 'description', 'enchantments', 'order']
    ordering = ['order']


# ================================================================
# ProductMonth Inline
# ================================================================
class ProductMonthInline(admin.TabularInline):
    model = ProductMonth
    extra = 1
    fields = [
        'months', 'original_price', 'discount_price',
        'wart_coin_price', 'image', 'description',
        'is_active', 'order'
    ]
    ordering = ['order', 'months']
    classes = ['product-month-inline']


# ================================================================
# Product Admin
# ================================================================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'image_thumbnail',
        'name_with_link',
        'category_with_link',
        'product_type_badge',
        'wart_coin_price_display',
        'available',
        'available_badge',
        'has_monthly_options_badge',
        'created_display',
    ]
    list_filter = [
        'available', 'created', 'category',
        'product_type', 'has_monthly_options'
    ]
    list_editable = ['available']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description', 'category__name']
    readonly_fields = ['image_preview', 'created', 'updated']
    ordering = ['-created']
    list_per_page = 25

    fieldsets = (
        ('اطلاعات محصول', {
            'fields': (
                'name', 'slug', 'category', 'product_type',
                'luckperms_group', 'description', 'specifications'
            ),
            'description': (
                '💡 برای رنک‌ها: luckperms_group نام دقیق گروه LuckPerms روی سرور است '
                '(مثلاً vip+). در specifications می‌توانید مشخصات را به فرمت '
                'fly : tick -- وارد کنید.'
            )
        }),
        ('قیمت و موجودی', {
            'fields': ('price', 'wart_coin_price', 'available', 'has_monthly_options'),
            'description': (
                '💡 قیمت قدیمی (price) فقط برای نمایش استفاده می‌شود. '
                'اگر has_monthly_options را فعال کنید، می‌توانید گزینه‌های ماهانه اضافه کنید.'
            )
        }),
        ('تصویر', {
            'fields': ('image', 'image_preview')
        }),
        ('اطلاعات سیستم', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )

    # --- Custom Display Methods ---

    def name_with_link(self, obj):
        url = reverse('admin:shop_product_change', args=[obj.pk])
        return format_html('<a href="{}">{}</a>', url, obj.name)
    name_with_link.short_description = 'نام محصول'
    name_with_link.admin_order_field = 'name'

    def category_with_link(self, obj):
        if obj.category:
            url = reverse('admin:shop_category_change', args=[obj.category.pk])
            return format_html(
                '<a href="{}" style="color: #4CAF50;">{}</a>',
                url, obj.category.name
            )
        return mark_safe('<span style="color: #999;">—</span>')
    category_with_link.short_description = 'دسته‌بندی'
    category_with_link.admin_order_field = 'category__name'

    def product_type_badge(self, obj):
        if obj.product_type == Product.PRODUCT_TYPE_RANK:
            return mark_safe(
                '<span style="background: linear-gradient(135deg, #FFD740, #FFC107); '
                'color: #1a1a1a; padding: 4px 12px; border-radius: 50px; '
                'font-weight: bold; font-size: 0.85rem;">🎖️ رنک</span>'
            )
        elif obj.product_type == Product.PRODUCT_TYPE_KIT:
            return mark_safe(
                '<span style="background: linear-gradient(135deg, #00E676, #00C853); '
                'color: white; padding: 4px 12px; border-radius: 50px; '
                'font-weight: bold; font-size: 0.85rem;">🧰 کیت</span>'
            )
        else:
            return mark_safe(
                '<span style="background: linear-gradient(135deg, #6C63FF, #5A52D5); '
                'color: white; padding: 4px 12px; border-radius: 50px; '
                'font-weight: bold; font-size: 0.85rem;">📦 معمولی</span>'
            )
    product_type_badge.short_description = 'نوع محصول'
    product_type_badge.admin_order_field = 'product_type'

    def wart_coin_price_display(self, obj):
        price_str = f"{obj.wart_coin_price:,.2f}"
        return format_html(
            '<span style="font-weight: bold; color: #FFD740; '
            'font-size: 1.1rem;">💰 {} WC</span>',
            price_str
        )
    wart_coin_price_display.short_description = 'قیمت (WC)'
    wart_coin_price_display.admin_order_field = 'wart_coin_price'

    def has_monthly_options_badge(self, obj):
        if obj.has_monthly_options:
            return mark_safe(
                '<span style="background: #4CAF50; color: white; '
                'padding: 3px 10px; border-radius: 15px; '
                'font-weight: bold;">✅ بله</span>'
            )
        return mark_safe(
            '<span style="background: #f44336; color: white; '
            'padding: 3px 10px; border-radius: 15px; '
            'font-weight: bold;">❌ خیر</span>'
        )
    has_monthly_options_badge.short_description = 'گزینه ماهانه'
    has_monthly_options_badge.admin_order_field = 'has_monthly_options'

    def image_thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" '
                'style="border-radius: 5px; object-fit: cover;" />',
                obj.image.url
            )
        return mark_safe('<span style="color: #9E9E9E;">بدون تصویر</span>')
    image_thumbnail.short_description = 'تصویر'

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="300" '
                'style="border-radius: 10px; margin-top: 10px;" />',
                obj.image.url
            )
        return mark_safe('<span style="color: #9E9E9E;">بدون تصویر</span>')
    image_preview.short_description = 'پیش‌نمایش تصویر'

    def available_badge(self, obj):
        if obj.available:
            return mark_safe(
                '<span style="background-color: #4CAF50; color: white; '
                'padding: 5px 15px; border-radius: 20px; '
                'font-weight: bold;">✅ موجود</span>'
            )
        return mark_safe(
            '<span style="background-color: #f44336; color: white; '
            'padding: 5px 15px; border-radius: 20px; '
            'font-weight: bold;">❌ ناموجود</span>'
        )
    available_badge.short_description = 'وضعیت'

    def created_display(self, obj):
        from django.utils import timezone
        if (timezone.now() - obj.created).days < 7:
            return format_html(
                '<span style="color: #007bff;">{} '
                '<span style="background: #ffc107; color: black; '
                'padding: 2px 6px; border-radius: 10px; '
                'font-size: 0.8em;">جدید</span></span>',
                obj.created.strftime("%Y-%m-%d")
            )
        return obj.created.strftime("%Y-%m-%d")
    created_display.short_description = 'تاریخ ایجاد'
    created_display.admin_order_field = 'created'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')

    def get_inlines(self, request, obj=None):
        inlines = []
        inlines.append(ProductMonthInline)
        if obj is None or obj.product_type == Product.PRODUCT_TYPE_KIT:
            inlines.append(KitItemInline)
        return inlines

    class Media:
        css = {'all': ('admin/css/product_admin.css',)}
        js = ('admin/js/product_admin.js',)


# ================================================================
# Product Inline for Category
# ================================================================
class ProductInline(admin.TabularInline):
    model = Product
    extra = 0
    fields = [
        'name', 'product_type', 'wart_coin_price',
        'available', 'image_thumbnail'
    ]
    readonly_fields = ['image_thumbnail']
    show_change_link = True

    def image_thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="40" height="40" '
                'style="border-radius: 3px; object-fit: cover;" />',
                obj.image.url
            )
        return mark_safe('<span style="color: #999;">—</span>')
    image_thumbnail.short_description = 'تصویر'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')


CategoryAdmin.inlines = [ProductInline]


# ================================================================
# ProductMonth Admin
# ================================================================
@admin.register(ProductMonth)
class ProductMonthAdmin(admin.ModelAdmin):
    list_display = [
        'product_link',
        'months_display',
        'wart_coin_price_display',
        'discount_display',
        'is_active',
        'is_active_badge',
        'order'
    ]
    list_filter = ['is_active', 'product__product_type', 'months']
    search_fields = ['product__name', 'description']
    list_editable = ['is_active', 'order']
    ordering = ['product', 'order', 'months']
    autocomplete_fields = ['product']

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('product', 'months', 'order', 'is_active'),
            'description': '💡 تعداد ماه و ترتیب نمایش را مشخص کنید'
        }),
        ('قیمت‌گذاری', {
            'fields': ('original_price', 'discount_price', 'wart_coin_price'),
            'description': (
                '💰 original_price و discount_price فقط برای نمایش تخفیف در سایت '
                'استفاده می‌شوند. wart_coin_price برای محاسبه واقعی خرید استفاده می‌شود.'
            )
        }),
        ('محتوای گزینه', {
            'fields': ('image', 'description'),
            'description': '🖼️ عکس و توضیحات کامل این گزینه ماهانه'
        }),
    )

    # --- Custom Display Methods ---

    def product_link(self, obj):
        if obj.product:
            url = reverse('admin:shop_product_change', args=[obj.product.pk])
            return format_html(
                '<a href="{}" style="color: #4CAF50; font-weight: bold;">{}</a>',
                url, obj.product.name
            )
        return mark_safe('<span style="color: #999;">—</span>')
    product_link.short_description = 'محصول'
    product_link.admin_order_field = 'product__name'

    def months_display(self, obj):
        return format_html(
            '<span style="background: linear-gradient(45deg, #4CAF50, #66BB6A); '
            'color: white; padding: 5px 15px; border-radius: 20px; '
            'font-weight: bold; font-size: 1.1rem;">📅 {} ماه</span>',
            obj.months
        )
    months_display.short_description = 'مدت'
    months_display.admin_order_field = 'months'

    def wart_coin_price_display(self, obj):
        price_str = f"{obj.wart_coin_price:,.2f}"
        return format_html(
            '<span style="font-weight: bold; color: #FFD740; '
            'font-size: 1.1rem;">💰 {} WC</span>',
            price_str
        )
    wart_coin_price_display.short_description = 'قیمت (WC)'
    wart_coin_price_display.admin_order_field = 'wart_coin_price'

    def discount_display(self, obj):
        if obj.has_discount():
            return format_html(
                '<span style="background: #f44336; color: white; '
                'padding: 3px 10px; border-radius: 15px; '
                'font-weight: bold;">🔥 {}% تخفیف</span>',
                obj.get_discount_percentage()
            )
        return mark_safe('<span style="color: #999;">—</span>')
    discount_display.short_description = 'تخفیف'

    def is_active_badge(self, obj):
        if obj.is_active:
            return mark_safe(
                '<span style="background: #4CAF50; color: white; '
                'padding: 3px 10px; border-radius: 15px;">✅ فعال</span>'
            )
        return mark_safe(
            '<span style="background: #f44336; color: white; '
            'padding: 3px 10px; border-radius: 15px;">❌ غیرفعال</span>'
        )
    is_active_badge.short_description = 'وضعیت نمایش'
    is_active_badge.admin_order_field = 'is_active'


# ================================================================
# SiteSettings Admin
# ================================================================
@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['site_name', 'navbar_title_display', 'updated']
    readonly_fields = ['updated']

    fieldsets = (
        ('اطلاعات عمومی', {
            'fields': ('site_name', 'navbar_title', 'footer_text', 'server_ip'),
        }),
        ('رنگ‌ها', {
            'fields': (
                'primary_color', 'secondary_color', 'accent_color',
                'dark_bg_color', 'card_bg_color',
                'text_light_color', 'text_muted_color'
            ),
        }),
        ('تصویر پس‌زمینه', {
            'fields': ('background_image',),
        }),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def navbar_title_display(self, obj):
        title = obj.navbar_title or obj.site_name or 'فروشگاه ماینکرفت'
        return format_html(
            '<span style="font-weight: bold; color: #4CAF50;">{}</span>',
            title
        )
    navbar_title_display.short_description = 'عنوان هدر'

    def get_queryset(self, request):
        SiteSettings.load()
        return super().get_queryset(request).filter(pk=1)