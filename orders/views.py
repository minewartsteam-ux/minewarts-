from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.conf import settings
from django.db import transaction
from cart.cart import Cart
from .forms import OrderCreateForm
from .models import OrderItem, Order
from accounts.models import WartCoin, WartCoinTransaction
import uuid
from decimal import Decimal
from .minecraft_service import apply_rank
@login_required
def order_create(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, 'سبد خرید شما خالی است.')
        return redirect('cart:cart_detail')
    
    # محاسبه قیمت کل به وارت کوین
    total_wart_coins = Decimal('0')
    for item in cart:
        if 'month_option' in item and item['month_option']:
            total_wart_coins += item['month_option'].get_wart_coin_price() * Decimal(str(item['quantity']))
        else:
            total_wart_coins += item['product'].wart_coin_price * Decimal(str(item['quantity']))
    
    # بررسی موجودی
    wallet, created = WartCoin.objects.get_or_create(user=request.user)
    if wallet.balance < total_wart_coins:
        messages.error(
            request,
            f'موجودی وارت کوین شما کافی نیست. موجودی شما: {wallet.balance:,.2f} WC، نیاز: {total_wart_coins:,.2f} WC'
        )
        return redirect('cart:cart_detail')
    
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            # استفاده از نام کاربری ماینکرفت از پروفایل کاربر
            from accounts.models import UserProfile
            user_profile, created = UserProfile.objects.get_or_create(user=request.user)
            
            if not user_profile.minecraft_username:
                messages.error(request, '⚠️ برای ثبت سفارش، باید نام کاربری ماینکرفت خود را در پروفایل تنظیم کنید.')
                return redirect('accounts:profile')
            
            minecraft_username = user_profile.minecraft_username.strip()
            
            try:
                with transaction.atomic():
                    # بررسی مجدد موجودی (برای جلوگیری از race condition)
                    wallet.refresh_from_db()
                    if wallet.balance < total_wart_coins:
                        messages.error(request, 'موجودی وارت کوین شما کافی نیست. لطفاً دوباره تلاش کنید.')
                        return redirect('cart:cart_detail')
                    
                    # ایجاد سفارش
                    order = form.save(commit=False)
                    order.user = request.user
                    order.email = request.user.email
                    order.minecraft_username = minecraft_username
                    order.transaction_id = str(uuid.uuid4())
                    order.wart_coin_amount = total_wart_coins
                    order.paid = True  # پرداخت با وارت کوین فوری است
                    order.payment_status = 'completed'
                    
                    order.save()
                    
                    # افزودن آیتم‌های سفارش
                    for item in cart:
                        if 'month_option' in item and item['month_option']:
                            wart_coin_price = item['month_option'].get_wart_coin_price()
                            month_option_id = item['month_option'].id
                        else:
                            wart_coin_price = item['product'].wart_coin_price
                            month_option_id = None
                        
                        OrderItem.objects.create(
                            order=order,
                            product=item['product'],
                            wart_coin_price=wart_coin_price,
                            quantity=item['quantity'],
                            month_option_id=month_option_id
                        )
                    
                    # کسر وارت کوین
                    wallet.deduct_coins(
                        amount=total_wart_coins,
                        reason=f'خرید سفارش #{order.id}',
                        transaction_type='spend'
                    )
                    
                    # اعمال رنک — صف امن با تلاش مجدد (غیرهمزمان)
                    if any(item['product'].product_type == 'rank' for item in cart):
                        apply_rank(order.id)
                        messages.info(
                            request,
                            'رنک شما در صف اعمال است و ظرف چند دقیقه روی سرور فعال می‌شود.',
                        )
                    
                    # ثبت تراکنش مرتبط با سفارش
                    transaction_obj = WartCoinTransaction.objects.filter(
                        wallet=wallet
                    ).order_by('-created').first()
                    if transaction_obj:
                        transaction_obj.related_order = order
                        transaction_obj.save()
                    
                    # پاک کردن سبد خرید
                    cart.clear()
                    
                    messages.success(request, f'✅ سفارش شما با موفقیت ثبت شد! شناسه سفارش: #{order.id}')
                    return redirect('orders:payment_success', order_id=order.id)
            except Exception as e:
                messages.error(request, f'❌ خطا در ثبت سفارش: {str(e)}')
                return redirect('cart:cart_detail')
    else:
        # پیش‌پر کردن فرم با اطلاعات کاربر
        form = OrderCreateForm(initial={
            'first_name': request.user.first_name or '',
            'last_name': request.user.last_name or '',
        })
    
    return render(request, 'orders/create.html', {
        'cart': cart,
        'form': form,
        'total_wart_coins': total_wart_coins,
        'wallet_balance': wallet.balance,
    })

@login_required
def payment(request, order_id):
    """این view دیگر استفاده نمی‌شود - پرداخت با وارت کوین است"""
    messages.info(request, 'پرداخت با وارت کوین انجام می‌شود. لطفاً از صفحه ایجاد سفارش استفاده کنید.')
    return redirect('orders:order_create')


@login_required
def payment_wart_coin(request, purchase_id):
    """پرداخت برای خرید وارت کوین با پول واقعی"""
    from accounts.models import WartCoinPurchase
    from .payment_gateway import ZarinpalPayment
    
    purchase = get_object_or_404(WartCoinPurchase, id=purchase_id, user=request.user)
    
    if purchase.payment_status == 'completed':
        messages.success(request, 'این خرید قبلاً پرداخت شده است.')
        return redirect('accounts:profile')
    
    if request.method == 'POST':
        try:
            zarinpal = ZarinpalPayment()
            # زرین‌پال قیمت را به ریال می‌خواهد، پس باید در 10 ضرب کنیم (تومان به ریال)
            amount = int(purchase.total_price * 10)  # تبدیل تومان به ریال
            
            if amount <= 0:
                messages.error(request, 'مبلغ خرید نامعتبر است.')
                return render(request, 'orders/payment_wart_coin.html', {'purchase': purchase})
            
            description = f'خرید {purchase.coin_amount} وارت کوین'
            callback_url = request.build_absolute_uri(
                reverse('orders:payment_wart_coin_callback', args=[purchase.id])
            )
            
            result = zarinpal.send_request(
                amount=amount,
                description=description,
                callback_url=callback_url,
                email=request.user.email
            )
            
            if result.get('status') == 'success':
                authority = result.get('authority')
                if authority:
                    request.session[f'wart_coin_purchase_authority_{purchase.id}'] = authority
                    request.session.modified = True
                    payment_url = result.get('payment_url')
                    if payment_url:
                        return redirect(payment_url)
                    else:
                        messages.error(request, 'خطا در دریافت لینک پرداخت.')
                else:
                    messages.error(request, 'خطا در دریافت کد پرداخت.')
            else:
                error_msg = result.get('message', 'خطای نامشخص در اتصال به درگاه پرداخت')
                messages.error(request, f'❌ {error_msg}')
        except Exception as e:
            messages.error(request, f'❌ خطا در پردازش پرداخت: {str(e)}')
    
    return render(request, 'orders/payment_wart_coin.html', {'purchase': purchase})


@login_required
def payment_wart_coin_callback(request, purchase_id):
    """Callback پرداخت خرید وارت کوین"""
    from accounts.models import WartCoinPurchase
    from .payment_gateway import ZarinpalPayment
    
    purchase = get_object_or_404(WartCoinPurchase, id=purchase_id, user=request.user)
    authority = request.GET.get('Authority')
    status = request.GET.get('Status')
    
    session_authority = request.session.get(f'wart_coin_purchase_authority_{purchase.id}')
    
    if not authority or authority != session_authority:
        messages.error(request, 'اطلاعات پرداخت نامعتبر است.')
        return redirect('accounts:profile')
    
    if status == 'OK':
        try:
            zarinpal = ZarinpalPayment()
            # زرین‌پال قیمت را به ریال می‌خواهد، پس باید در 10 ضرب کنیم (تومان به ریال)
            amount = int(purchase.total_price * 10)  # تبدیل تومان به ریال
            result = zarinpal.verify_payment(amount=amount, authority=authority)
            
            if result.get('status') == 'success':
                purchase.mark_completed(payment_id=result.get('ref_id'))
                
                if f'wart_coin_purchase_authority_{purchase.id}' in request.session:
                    del request.session[f'wart_coin_purchase_authority_{purchase.id}']
                
                messages.success(request, f'✅ پرداخت موفق! {purchase.coin_amount} وارت کوین به حساب شما اضافه شد.')
                return redirect('accounts:profile')
            else:
                purchase.payment_status = 'failed'
                purchase.save()
                messages.error(request, f'❌ پرداخت ناموفق بود: {result.get("message", "خطای نامشخص")}')
                return redirect('accounts:profile')
        except Exception as e:
            purchase.payment_status = 'failed'
            purchase.save()
            messages.error(request, f'❌ خطا در پردازش پرداخت: {str(e)}')
            return redirect('accounts:profile')
    else:
        purchase.payment_status = 'cancelled'
        purchase.save()
        messages.warning(request, 'پرداخت توسط شما لغو شد.')
        return redirect('accounts:profile')

@login_required
def payment_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, paid=True)
    # بررسی اینکه سفارش متعلق به کاربر فعلی است
    if order.email != request.user.email:
        messages.error(request, 'شما اجازه دسترسی به این سفارش را ندارید.')
        return redirect('shop:product_list')
    return render(request, 'orders/payment_success.html', {'order': order})

# payment_callback دیگر استفاده نمی‌شود - پرداخت با وارت کوین است

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    # بررسی اینکه سفارش متعلق به کاربر فعلی است
    if not request.user.is_staff and order.user != request.user:
        messages.error(request, 'شما اجازه دسترسی به این سفارش را ندارید.')
        return redirect('shop:product_list')
    return render(request, 'orders/payment_user.html', {'order': order})
#from .minecraft_service import apply_rank