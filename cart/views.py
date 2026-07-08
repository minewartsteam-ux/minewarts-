from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from shop.models import Product, ProductMonth
from .cart import Cart
from .forms import CartAddProductForm

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    
    # دریافت و اعتبارسنجی داده‌ها
    try:
        quantity_str = request.POST.get('quantity', '1').strip()
        quantity = int(quantity_str)
        if quantity < 1:
            quantity = 1
        elif quantity > 20:
            quantity = 20
    except (ValueError, TypeError, AttributeError):
        quantity = 1
    
    # پردازش override - اگر string 'false' باشد، باید False شود
    override_str = request.POST.get('override', 'false')
    if isinstance(override_str, str):
        override = override_str.lower() in ('true', '1', 'on')
    else:
        override = bool(override_str)
    
    # دریافت گزینه ماهانه (فقط برای محصولاتی که نوع آن‌ها رنک است و گزینه ماهانه دارند)
    month_option = None
    month_option_id = request.POST.get('month_option_id', '').strip()
    if (
        month_option_id
        and getattr(product, 'product_type', None) == getattr(Product, 'PRODUCT_TYPE_RANK', 'rank')
        and getattr(product, 'has_monthly_options', False)
    ):
        try:
            month_option = ProductMonth.objects.get(
                id=int(month_option_id),
                product=product,
                is_active=True,
            )
        except (ProductMonth.DoesNotExist, ValueError, TypeError):
            month_option = None
            messages.warning(request, 'گزینه ماهانه انتخاب‌شده معتبر نبود؛ قیمت پایه اعمال شد.')
    
    # افزودن به سبد خرید
    try:
        cart.add(product=product, quantity=quantity, override_quantity=override, month_option=month_option)
        if month_option:
            messages.success(request, f'✅ {product.name} ({month_option.months} ماه) به سبد خرید اضافه شد!')
        else:
            messages.success(request, f'✅ {product.name} به سبد خرید اضافه شد!')
    except Exception as e:
        messages.error(request, f'❌ خطا در افزودن محصول: {str(e)}')
    
    return redirect('cart:cart_detail')

def cart_remove(request, product_id):
    """حذف محصول از سبد خرید - بدون نیاز به POST"""
    cart = Cart(request)
    try:
        product = get_object_or_404(Product, id=product_id)
        month_option_id = request.GET.get('month_option_id', '').strip()
        month_option_id_int = None
        if month_option_id:
            try:
                month_option_id_int = int(month_option_id)
            except (ValueError, TypeError):
                pass
        cart.remove(product, month_option_id=month_option_id_int)
        messages.success(request, f'✅ {product.name} از سبد خرید حذف شد!')
    except Exception as e:
        messages.error(request, f'❌ خطا در حذف محصول: {str(e)}')
    return redirect('cart:cart_detail')

def cart_detail(request):
    cart = Cart(request)
    for item in cart:
        item['update_quantity_form'] = CartAddProductForm(initial={'quantity': item['quantity'], 'override': True})
    return render(request, 'cart/detail.html', {'cart': cart})