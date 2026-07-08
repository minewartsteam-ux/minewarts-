from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.utils.safestring import mark_safe
from django.shortcuts import render
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from .models import Order, OrderItem, RankProvisionJob
from shop.models import Product, Category

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0
    readonly_fields = ['get_item_total']
    
    def get_item_total(self, obj):
        if obj.pk:
            return f"💰 {obj.get_cost():,.2f} WC"
        return "-"
    get_item_total.short_description = 'جمع آیتم (وارت کوین)'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer_name', 'minecraft_username_display', 'email', 'total_wart_coin_cost', 'rank_status_badge', 'payment_status_badge', 'paid_badge', 'created', 'view_order_link']
    list_filter = ['paid', 'payment_status', 'created', 'updated']
    search_fields = ['first_name', 'last_name', 'email', 'minecraft_username', 'transaction_id', 'id']
    readonly_fields = ['id', 'user', 'transaction_id', 'created', 'updated', 'total_cost_display', 'order_items_display']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('اطلاعات مشتری', {
            'fields': ('user', 'first_name', 'last_name', 'email', 'minecraft_username')
        }),
        ('اطلاعات پرداخت', {
            'fields': ('paid', 'payment_status', 'wart_coin_amount', 'transaction_id')
        }),
        ('وضعیت رنک ماینکرفت', {
            'fields': ('rank_applied', 'rank_error'),
        }),
        ('اطلاعات سفارش', {
            'fields': ('id', 'created', 'updated', 'total_cost_display')
        }),
        ('محصولات سفارش', {
            'fields': ('order_items_display',)
        }),
    )
    
    def customer_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    customer_name.short_description = 'نام مشتری'
    customer_name.admin_order_field = 'first_name'
    
    def minecraft_username_display(self, obj):
        if obj.minecraft_username:
            return format_html(
                '<span style="background: #4CAF50; color: white; padding: 3px 10px; border-radius: 15px; font-weight: bold;">🎮 {}</span>',
                obj.minecraft_username
            )
        return format_html('<span style="color: #999;">-</span>', '')
    minecraft_username_display.short_description = 'Minecraft Username'
    
    def total_wart_coin_cost(self, obj):
        if obj.pk:
            return format_html(
                '<span style="font-weight: bold; color: #4CAF50;">💰 {} WC</span>',
                f"{obj.get_total_wart_coin_cost():,.2f}"
            )
        return "-"
    total_wart_coin_cost.short_description = 'جمع کل (وارت کوین)'
    
    def total_cost(self, obj):
        if obj.pk:
            return f"💰 {obj.get_total_wart_coin_cost():,.2f} WC"
        return "-"
    total_cost.short_description = 'جمع کل (وارت کوین)'
    
    def total_cost_display(self, obj):
        if obj.pk:
            return format_html(
                '<span style="font-size: 1.3rem; font-weight: bold; color: #4CAF50;">💰 {} WC</span>',
                f"{obj.get_total_wart_coin_cost():,.2f}"
            )
        return "-"
    total_cost_display.short_description = 'جمع کل سفارش (وارت کوین)'
    
    def payment_status_badge(self, obj):
        colors = {
            'pending': '#FFC107',
            'completed': '#4CAF50',
            'failed': '#f44336',
            'cancelled': '#9E9E9E',
        }
        color = colors.get(obj.payment_status, '#9E9E9E')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold;">{}</span>',
            color,
            obj.get_payment_status_display()
        )
    payment_status_badge.short_description = 'وضعیت پرداخت'
    
    def paid_badge(self, obj):
        if obj.paid:
            return format_html(
                '<span style="background-color: #4CAF50; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold;">✅ پرداخت شده</span>',
                ''
            )
        return format_html(
            '<span style="background-color: #FFC107; color: #000; padding: 5px 15px; border-radius: 20px; font-weight: bold;">⏳ در انتظار</span>',
            ''
        )
    paid_badge.short_description = 'پرداخت'

    def rank_status_badge(self, obj):
        if obj.rank_applied:
            return format_html(
                '<span style="background-color: #4CAF50; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold;">✅ رنک اعمال شد</span>',
                ''
            )
        if obj.rank_error:
            return format_html(
                '<span style="background-color: #f44336; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold;">❌ خطا</span>',
                ''
            )
        has_rank = obj.items.filter(product__product_type='rank').exists()
        if has_rank:
            return format_html(
                '<span style="background-color: #FFC107; color: #000; padding: 5px 15px; border-radius: 20px; font-weight: bold;">⏳ در صف</span>',
                ''
            )
        # ✅ اصلاح: اضافه کردن آرگومان دوم خالی
        return format_html('<span style="color: #999;">—</span>', '')
    rank_status_badge.short_description = 'رنک'

    def order_items_display(self, obj):
        if not obj.pk:
            return "-"
        items_html = '<div style="max-height: 300px; overflow-y: auto;">'
        for item in obj.items.all():
            items_html += f'''
                <div style="border: 1px solid #ddd; padding: 10px; margin: 5px 0; border-radius: 5px; background: rgba(255,255,255,0.05);">
                    <strong>{item.product.name}</strong><br>
                    <small>تعداد: {item.quantity} × قیمت: 💰 {item.wart_coin_price:,.2f} WC = 💰 {item.get_cost():,.2f} WC</small>
                </div>
            '''
        items_html += '</div>'
        return mark_safe(items_html)
    order_items_display.short_description = 'محصولات'
    
    def view_order_link(self, obj):
        if obj.pk:
            url = reverse('orders:order_detail', args=[obj.id])
            return format_html('<a href="{}" target="_blank" style="background: #2196F3; color: white; padding: 5px 15px; border-radius: 20px; text-decoration: none;">مشاهده</a>', url)
        return "-"
    view_order_link.short_description = 'مشاهده سفارش'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('items', 'items__product')


@admin.register(RankProvisionJob)
class RankProvisionJobAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'status', 'attempts', 'next_retry_at', 'created', 'updated']
    list_filter = ['status', 'created']
    search_fields = ['idempotency_key', 'order__id', 'order__minecraft_username', 'last_error']
    readonly_fields = ['idempotency_key', 'payload', 'rcon_response', 'created', 'updated']
    ordering = ['-created']

    actions = ['retry_selected_jobs']

    @admin.action(description='تلاش مجدد برای jobs انتخاب‌شده')
    def retry_selected_jobs(self, request, queryset):
        from orders.rank_provisioning import process_rank_job
        count = 0
        for job in queryset.exclude(status=RankProvisionJob.STATUS_APPLIED):
            job.status = RankProvisionJob.STATUS_PENDING
            job.next_retry_at = None
            job.save(update_fields=['status', 'next_retry_at', 'updated'])
            process_rank_job(job.id)
            count += 1
        self.message_user(request, f'{count} job(s) re-queued.')

# ایجاد view برای Dashboard
def admin_dashboard(request):
    # بررسی دسترسی staff
    if not request.user.is_staff:
        from django.http import Http404
        raise Http404("دسترسی به این صفحه برای شما امکان‌پذیر نیست.")
    
    # آمار کلی - بهینه‌سازی با یک کوئری
    total_orders = Order.objects.count()
    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    
    # محاسبه مجموع وارت کوین استفاده شده در سفارشات پرداخت شده
    paid_orders = Order.objects.filter(paid=True).prefetch_related('items', 'items__product')
    total_revenue = sum([float(order.get_total_wart_coin_cost()) for order in paid_orders]) if paid_orders else 0
    
    # آمار امروز - بهینه‌سازی
    today = timezone.now().date()
    today_orders_qs = Order.objects.filter(created__date=today)
    today_orders = today_orders_qs.count()
    today_paid_orders = today_orders_qs.filter(paid=True).prefetch_related('items', 'items__product')
    today_revenue = sum([float(order.get_total_wart_coin_cost()) for order in today_paid_orders]) if today_paid_orders else 0
    
    # آمار هفته گذشته - بهینه‌سازی
    week_ago = today - timedelta(days=7)
    week_orders_qs = Order.objects.filter(created__date__gte=week_ago)
    week_orders = week_orders_qs.count()
    week_paid_orders = week_orders_qs.filter(paid=True).prefetch_related('items', 'items__product')
    week_revenue = sum([float(order.get_total_wart_coin_cost()) for order in week_paid_orders]) if week_paid_orders else 0
    
    # آخرین سفارشات - بهینه‌سازی با select_related
    recent_orders = Order.objects.select_related().prefetch_related('items', 'items__product').order_by('-created')[:10]
    
    # محصولات پرفروش - بهینه‌سازی
    top_products = Product.objects.annotate(
        total_sold=Count('order_items')
    ).order_by('-total_sold')[:5]
    
    # وضعیت پرداخت - بهینه‌سازی با یک کوئری
    payment_stats = {
        'paid': Order.objects.filter(paid=True).count(),
        'pending': Order.objects.filter(paid=False, payment_status='pending').count(),
        'failed': Order.objects.filter(payment_status='failed').count(),
    }
    
    context = {
        'total_orders': total_orders,
        'total_products': total_products,
        'total_categories': total_categories,
        'total_revenue': total_revenue,
        'today_orders': today_orders,
        'today_revenue': today_revenue,
        'week_orders': week_orders,
        'week_revenue': week_revenue,
        'recent_orders': recent_orders,
        'top_products': top_products,
        'payment_stats': payment_stats,
    }
    
    return render(request, 'admin/dashboard.html', context)