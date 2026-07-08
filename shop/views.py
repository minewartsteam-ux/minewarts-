from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import Product, Category
from cart.forms import CartAddProductForm
from orders.models import Order
from accounts.models import WartCoinTransaction


def product_list(request, category_slug=None):
    """نمایش لیست محصولات و دسته‌بندی‌ها"""
    categories = Category.objects.filter(parent=None)  # فقط دسته‌بندی‌های اصلی
    category = None
    products = None
    category_bg_image = None
    cart_add_product_form = CartAddProductForm()

    # محاسبه تعداد محصولات موجود برای هر دسته‌بندی (فقط دسته‌های اصلی)
    categories_with_count = []
    for cat in categories:
        # شمارش محصولات در دسته اصلی و زیرمجموعه‌هایش
        subcategories = Category.objects.filter(parent=cat)
        all_category_ids = [cat.id] + list(subcategories.values_list('id', flat=True))
        count = Product.objects.filter(category_id__in=all_category_ids, available=True).count()
        categories_with_count.append({
            'category': cat,
            'count': count
        })

    # اگر دسته‌بندی انتخاب شده باشد، محصولات آن را نمایش بده
    if category_slug:
        try:
            category = get_object_or_404(Category, slug=category_slug)
            # اگر دسته اصلی است، محصولات خودش و زیرمجموعه‌هایش را نشان بده
            if category.parent is None:
                subcategories = Category.objects.filter(parent=category)
                all_category_ids = [category.id] + list(subcategories.values_list('id', flat=True))
                products = Product.objects.filter(category_id__in=all_category_ids, available=True)
            else:
                # اگر زیرمجموعه است، فقط محصولات خودش را نشان بده
                products = Product.objects.filter(category=category, available=True)
            
            if category.image:
                category_bg_image = category.image.url
        except Category.DoesNotExist:
            category = None
            products = None

    return render(request, 'shop/product_list.html', {
        'category': category,
        'categories': categories,
        'categories_with_count': categories_with_count,
        'products': products,
        'category_bg_image': category_bg_image,
        'cart_add_product_form': cart_add_product_form,
    })


def server_ip_view(request):
    """نمایش آی‌پی/دامنه سرور از تنظیمات سایت"""
    return render(request, 'shop/server_ip.html')


def product_detail(request, slug):
    """نمایش جزئیات یک محصول"""
    product = get_object_or_404(Product, slug=slug, available=True)
    cart_add_product_form = CartAddProductForm()
    
    # گزینه‌های ماهانه فقط برای محصولاتی که نوع آن‌ها "رنک" است و has_monthly_options فعال است
    if (
        getattr(product, 'product_type', None) == getattr(Product, 'PRODUCT_TYPE_RANK', 'rank')
        and product.has_monthly_options
    ):
        monthly_options = product.monthly_options.filter(is_active=True).order_by('order', 'months')
    else:
        monthly_options = product.monthly_options.none()
    
    return render(request, 'shop/product_detail.html', {
        'product': product,
        'cart_add_product_form': cart_add_product_form,
        'monthly_options': monthly_options,
    })


def product_monthly_options(request, slug):
    """صفحه جداگانه برای نمایش گزینه‌های ماهانه محصول"""
    product = get_object_or_404(Product, slug=slug, available=True)
    
    # فقط برای محصولات نوع "رنک" اجازه نمایش گزینه‌های ماهانه را بده
    if (
        getattr(product, 'product_type', None) == getattr(Product, 'PRODUCT_TYPE_RANK', 'rank')
        and product.has_monthly_options
    ):
        monthly_options = product.monthly_options.filter(is_active=True).order_by('order', 'months')
    else:
        monthly_options = product.monthly_options.none()

    if not monthly_options.exists():
        messages.warning(request, 'این محصول گزینه‌های ماهانه فعال ندارد.')
        return redirect('shop:product_detail', slug=slug)
    
    cart_add_product_form = CartAddProductForm()
    
    return render(request, 'shop/product_monthly_options.html', {
        'product': product,
        'monthly_options': monthly_options,
        'cart_add_product_form': cart_add_product_form,
    })


def product_specifications(request, slug):
    """صفحه مشخصات کامل محصول - بدون گزینه‌های ماهانه"""
    product = get_object_or_404(Product, slug=slug, available=True)
    cart_add_product_form = CartAddProductForm()
    
    return render(request, 'shop/product_specifications.html', {
        'product': product,
        'cart_add_product_form': cart_add_product_form,
    })


# ================================================================
# 🔹 ویوهای داشبورد ادمین (برای پنل مدیریت)
# ================================================================

@staff_member_required
def admin_dashboard(request):
    """داشبورد مدیریت با آمار کامل"""
    
    try:
        # آمار کلی
        total_orders = Order.objects.count()
        total_products = Product.objects.count()
        total_categories = Category.objects.count()
        
        # محاسبه درآمد کل از تراکنش‌ها
        total_revenue = WartCoinTransaction.objects.filter(
            transaction_type='purchase'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # آمار امروز
        today = timezone.now().date()
        today_start = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
        today_end = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.max.time()))
        
        today_orders = Order.objects.filter(created__range=(today_start, today_end)).count()
        today_revenue = WartCoinTransaction.objects.filter(
            transaction_type='purchase',
            created__range=(today_start, today_end)
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # آمار هفته
        week_ago = timezone.now() - timedelta(days=7)
        week_orders = Order.objects.filter(created__gte=week_ago).count()
        week_revenue = WartCoinTransaction.objects.filter(
            transaction_type='purchase',
            created__gte=week_ago
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # وضعیت پرداخت
        payment_stats = {
            'paid': Order.objects.filter(paid=True).count(),
            'pending': Order.objects.filter(paid=False).count(),
            'failed': 0,
        }
        
        # محصولات پرفروش
        top_products = Product.objects.annotate(
            total_sold=Sum('orderitem__quantity')
        ).filter(total_sold__gt=0).order_by('-total_sold')[:5]
        
        # آخرین سفارشات
        recent_orders = Order.objects.all().order_by('-created')[:10]
        
        context = {
            'total_orders': total_orders,
            'total_products': total_products,
            'total_categories': total_categories,
            'total_revenue': total_revenue,
            'today_orders': today_orders,
            'today_revenue': today_revenue,
            'week_orders': week_orders,
            'week_revenue': week_revenue,
            'payment_stats': payment_stats,
            'top_products': top_products,
            'recent_orders': recent_orders,
            'title': 'داشبورد مدیریت',
        }
        
        return render(request, 'admin/dashboard.html', context)
        
    except Exception as e:
        # در صورت خطا، یک صفحه ساده با خطا نمایش بده
        return render(request, 'admin/dashboard.html', {
            'error': str(e),
            'title': 'خطا در داشبورد'
        })