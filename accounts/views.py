from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_protect
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.core.mail import send_mail, EmailMultiAlternatives
from django.core.cache import cache
from django.conf import settings
from django.urls import reverse
from django.http import JsonResponse
from django.db import transaction
from decimal import Decimal
import random
import uuid

from .forms import (
    CustomUserCreationForm,
    CustomAuthenticationForm,
    SupportTicketCreateForm,
    SupportMessageForm,
)
from .models import (
    SupportTicket, SupportMessage,
    WartCoin, WartCoinPurchase, WartCoinTransaction,
    WartCoinSettings, BulkDiscount, SiteInfo, UserProfile,
    Currency, CurrencyWallet, CurrencyTransaction,
    CurrencySettings, CurrencyPurchase
)
from .tokens import account_activation_token

User = get_user_model()


# ============================================================
# 📧 ارسال کد تایید (فقط کد، بدون دکمه)
# ============================================================

def send_verification_code(user):
    """ارسال کد 6 رقمی تایید ایمیل - فقط کد، بدون دکمه"""
    rate_key = f'email_code_rate_{user.email}'
    if cache.get(rate_key):
        raise Exception('لطفاً ۶۰ ثانیه صبر کنید تا کد جدید درخواست دهید.')
    
    code = str(random.randint(100000, 999999))
    cache_key = f'email_verification_code_{user.email}'
    cache.set(cache_key, code, 900)
    cache.set(rate_key, True, 60)
    
    site_name = getattr(settings, 'SITE_NAME', 'Mine Warts')
    user_name = user.get_full_name() or user.username

    html_message = f"""
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>کد تایید</title>
        <style>
            body {{ font-family: Tahoma, Arial; direction: rtl; background: #0a0a0f; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }}
            .container {{ max-width: 420px; width: 100%; background: #14141e; border-radius: 20px; padding: 35px 30px; border: 1px solid rgba(76,175,80,0.12); text-align: center; }}
            .icon {{ font-size: 42px; }}
            h1 {{ color: #fff; font-size: 20px; margin: 10px 0 4px; }}
            .subtitle {{ color: rgba(255,255,255,0.25); font-size: 12px; }}
            .divider {{ width: 30px; height: 2px; background: #4CAF50; margin: 12px auto 20px; border-radius: 2px; }}
            .greeting {{ color: rgba(255,255,255,0.7); font-size: 14px; margin-bottom: 6px; }}
            .greeting strong {{ color: #fff; }}
            .message {{ color: rgba(255,255,255,0.4); font-size: 13px; margin-bottom: 22px; }}
            .code-box {{ font-family: 'Courier New', monospace; font-size: 38px; font-weight: 800; letter-spacing: 12px; color: #4CAF50; background: rgba(76,175,80,0.06); padding: 14px 10px; border-radius: 12px; border: 1px solid rgba(76,175,80,0.1); direction: ltr; }}
            .info {{ color: rgba(255,255,255,0.2); font-size: 12px; margin-top: 16px; }}
            .info strong {{ color: #FFC107; }}
            .footer {{ margin-top: 24px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.04); color: rgba(255,255,255,0.1); font-size: 11px; }}
            .footer span {{ color: #4CAF50; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="icon">🔐</div>
            <h1>کد تایید</h1>
            <div class="subtitle">{site_name}</div>
            <div class="divider"></div>
            <p class="greeting">سلام <strong>{user_name}</strong></p>
            <p class="message">برای فعال‌سازی حساب، کد زیر را وارد کنید</p>
            <div class="code-box">{code}</div>
            <p class="info">⏱️ اعتبار: <strong>۱۵ دقیقه</strong></p>
            <p class="info">🔒 این کد محرمانه است</p>
            <div class="footer">✦ <span>{site_name}</span> ✦</div>
        </div>
    </body>
    </html>
    """
    text_message = f"""
    🔐 کد تایید - {site_name}
    
    سلام {user_name}
    
    کد تایید شما:
    {code}
    
    ⏱️ اعتبار: ۱۵ دقیقه
    🔒 این کد محرمانه است
    """
    
    try:
        email = EmailMultiAlternatives(
            subject=f'کد تایید - {site_name}',
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)
    except Exception:
        send_mail(
            subject=f'کد تایید - {site_name}',
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
    
    return code


# ============================================================
# 📝 ثبت‌نام
# ============================================================

@require_http_methods(["GET", "POST"])
@csrf_protect
def register_view(request):
    if request.user.is_authenticated:
        return redirect('shop:product_list')
    
    pending_user_id = request.session.get('pending_user_id')
    pending_email = request.session.get('pending_user_email')
    if pending_user_id and pending_email:
        try:
            pending_user = User.objects.get(id=pending_user_id, email=pending_email)
            if not pending_user.is_active:
                messages.info(request, 'کد تایید قبلی هنوز معتبر است.')
                return redirect('accounts:verify_code')
        except User.DoesNotExist:
            request.session.pop('pending_user_id', None)
            request.session.pop('pending_user_email', None)
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            
            try:
                send_verification_code(user)
                request.session['pending_user_id'] = user.id
                request.session['pending_user_email'] = user.email
                messages.success(request, '✅ کد تایید به ایمیل شما ارسال شد.')
                return redirect('accounts:verify_code')
            except Exception as e:
                messages.error(request, f'❌ خطا: {str(e)}')
                user.delete()
                return redirect('accounts:register')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'❌ {error}')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


# ============================================================
# ✅ تایید کد
# ============================================================

@require_http_methods(["GET", "POST"])
@csrf_protect
def verify_code_view(request):
    pending_user_id = request.session.get('pending_user_id')
    pending_email = request.session.get('pending_user_email')
    
    if not pending_user_id or not pending_email:
        messages.error(request, 'لطفاً ابتدا ثبت‌نام کنید.')
        return redirect('accounts:register')
    
    try:
        user = User.objects.get(id=pending_user_id, email=pending_email)
    except User.DoesNotExist:
        messages.error(request, 'کاربر یافت نشد.')
        request.session.pop('pending_user_id', None)
        request.session.pop('pending_user_email', None)
        return redirect('accounts:register')
    
    if user.is_active:
        messages.info(request, 'حساب شما قبلاً فعال شده است.')
        request.session.pop('pending_user_id', None)
        request.session.pop('pending_user_email', None)
        return redirect('accounts:login')
    
    error = None
    
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        cache_key = f'email_verification_code_{user.email}'
        real_code = cache.get(cache_key)
        
        attempt_key = f'verify_code_attempts_{user.email}'
        attempts = cache.get(attempt_key, 0)
        
        if attempts >= 5:
            error = '❌ تعداد تلاش‌ها بیش از حد مجاز است.'
        elif not code:
            error = '❌ کد را وارد کنید.'
            cache.set(attempt_key, attempts + 1, 900)
        elif len(code) != 6 or not code.isdigit():
            error = '❌ کد باید ۶ رقم باشد.'
            cache.set(attempt_key, attempts + 1, 900)
        elif not real_code or code != real_code:
            error = '❌ کد اشتباه است.'
            cache.set(attempt_key, attempts + 1, 900)
        else:
            user.is_active = True
            user.save(update_fields=['is_active'])
            cache.delete(cache_key)
            cache.delete(attempt_key)
            request.session.pop('pending_user_id', None)
            request.session.pop('pending_user_email', None)
            messages.success(request, '✅ ایمیل تایید شد. حالا وارد شوید.')
            return redirect('accounts:login')
    
    return render(request, 'accounts/verify_code.html', {
        'error': error,
        'email': user.email,
    })


# ============================================================
# 🔄 ارسال مجدد کد (AJAX)
# ============================================================

@require_http_methods(["POST"])
@csrf_protect
def resend_code_view(request):
    pending_user_id = request.session.get('pending_user_id')
    pending_email = request.session.get('pending_user_email')
    
    if not pending_user_id or not pending_email:
        return JsonResponse({
            'success': False,
            'error': 'اطلاعات کاربر یافت نشد.'
        }, status=400)
    
    try:
        user = User.objects.get(id=pending_user_id, email=pending_email)
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'کاربر یافت نشد.'
        }, status=404)
    
    if user.is_active:
        return JsonResponse({
            'success': False,
            'error': 'حساب شما قبلاً فعال شده است.'
        }, status=400)
    
    rate_key = f'resend_rate_{user.email}'
    if cache.get(rate_key):
        return JsonResponse({
            'success': False,
            'error': 'لطفاً ۶۰ ثانیه صبر کنید.'
        }, status=429)
    
    try:
        send_verification_code(user)
        cache.set(rate_key, True, 60)
        return JsonResponse({
            'success': True,
            'message': 'کد جدید با موفقیت ارسال شد.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ============================================================
# 👤 ورود
# ============================================================

@require_http_methods(["GET", "POST"])
@csrf_protect
def login_view(request):
    if request.user.is_authenticated:
        return redirect('shop:product_list')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            if not user.is_active:
                try:
                    send_verification_code(user)
                    request.session['pending_user_id'] = user.id
                    request.session['pending_user_email'] = user.email
                    messages.warning(request, 'حساب شما فعال نیست. کد جدید ارسال شد.')
                    return redirect('accounts:verify_code')
                except Exception as e:
                    messages.error(request, f'خطا: {str(e)}')
                    return redirect('accounts:login')
            
            login(request, user)
            messages.success(request, f'خوش آمدید {user.get_full_name() or user.username}!')
            return redirect(request.GET.get('next', 'shop:product_list'))
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})


@login_required
@require_http_methods(["POST"])
@csrf_protect
def logout_view(request):
    name = request.user.get_full_name() or request.user.username
    logout(request)
    messages.success(request, f'خداحافظ {name}!')
    return redirect('shop:product_list')


# ============================================================
# 👤 پروفایل
# ============================================================

@login_required
@require_http_methods(["GET", "POST"])
@csrf_protect
def profile_view(request):
    # گرفتن یا ساختن پروفایل
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # گرفتن یا ساختن کیف پول وارت کوین
    wallet, created = WartCoin.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        minecraft_username = request.POST.get('minecraft_username', '').strip()
        if not minecraft_username:
            messages.error(request, 'نام کاربری ماینکرفت نمی‌تواند خالی باشد.')
        else:
            import re
            if not re.match(r'^[a-zA-Z0-9_]{1,16}$', minecraft_username):
                messages.error(request, 'نام کاربری ماینکرفت نامعتبر است.')
            else:
                profile.minecraft_username = minecraft_username
                profile.save()
                messages.success(request, '✅ به‌روزرسانی شد.')
                return redirect('accounts:profile')
    
    return render(request, 'accounts/profile.html', {
        'user': request.user,
        'profile': profile,
        'wart_coin_balance': wallet.balance,  # موجودی وارت کوین
    })


# ============================================================
# 🎫 تیکت‌ها (پشتیبانی با وضعیت‌های کامل)
# ============================================================

@login_required
def ticket_list(request):
    tickets = SupportTicket.objects.filter(user=request.user).order_by('-updated')
    return render(request, 'accounts/ticket_list.html', {'tickets': tickets})


@login_required
@require_http_methods(["GET", "POST"])
@csrf_protect
def ticket_create(request):
    if request.method == 'POST':
        form = SupportTicketCreateForm(request.POST)
        message_form = SupportMessageForm(request.POST)
        
        if form.is_valid() and message_form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.status = 'new'
            ticket.save()
            
            first_message = message_form.save(commit=False)
            first_message.ticket = ticket
            first_message.sender = request.user
            first_message.is_staff = False
            first_message.save()
            
            messages.success(request, '✅ تیکت با موفقیت ثبت شد.')
            return redirect('accounts:ticket_detail', ticket_id=ticket.id)
    else:
        form = SupportTicketCreateForm()
        message_form = SupportMessageForm()
    
    return render(request, 'accounts/ticket_create.html', {
        'form': form,
        'message_form': message_form,
    })


@login_required
@require_http_methods(["GET", "POST"])
@csrf_protect
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)
    
    # ===== بررسی خودکار وضعیت هنگام باز کردن تیکت =====
    if ticket.status != 'closed':
        ticket.update_status_based_on_last_message()
    
    if request.method == 'POST':
        form = SupportMessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.ticket = ticket
            msg.sender = request.user
            msg.is_staff = request.user.is_staff
            msg.save()
            
            # ===== به‌روزرسانی وضعیت بر اساس آخرین پیام =====
            ticket.update_status_based_on_last_message()
            
            messages.success(request, '✅ پیام ارسال شد.')
            return redirect('accounts:ticket_detail', ticket_id=ticket.id)
    else:
        form = SupportMessageForm()
    
    messages_qs = ticket.messages.select_related('sender').order_by('created')
    return render(request, 'accounts/ticket_detail.html', {
        'ticket': ticket,
        'messages': messages_qs,
        'form': form,
        'is_support_panel': False,
    })


# ===== تابع staff_check =====
def staff_check(user):
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    try:
        return user.assigned_tickets.exists()
    except AttributeError:
        return SupportTicket.objects.filter(assigned_admins=user).exists()


@login_required
@user_passes_test(staff_check)
def support_panel_dashboard(request):
    status = request.GET.get('status')
    
    if request.user.is_staff:
        tickets = SupportTicket.objects.all()
    else:
        tickets = SupportTicket.objects.filter(assigned_admins=request.user)
    
    tickets = tickets.order_by('-updated')
    if status in dict(SupportTicket.STATUS_CHOICES).keys():
        tickets = tickets.filter(status=status)
    
    return render(request, 'accounts/support_panel_dashboard.html', {
        'tickets': tickets,
        'current_status': status,
    })


@login_required
@user_passes_test(staff_check)
@require_http_methods(["GET", "POST"])
@csrf_protect
def support_panel_ticket_detail(request, ticket_id):
    ticket = get_object_or_404(SupportTicket, id=ticket_id)
    
    if not request.user.is_staff and request.user not in ticket.assigned_admins.all():
        messages.error(request, 'شما دسترسی ندارید.')
        return redirect('accounts:support_panel_dashboard')
    
    # ===== بررسی خودکار وضعیت هنگام باز کردن تیکت =====
    if ticket.status != 'closed':
        ticket.update_status_based_on_last_message()
    
    # ===== مدیریت اکشن‌های بستن و باز کردن =====
    action = request.GET.get('action')
    if action == 'close':
        if ticket.status != 'closed':
            ticket.close()
            messages.success(request, f'✅ تیکت #{ticket.id} با موفقیت بسته شد.')
        else:
            messages.info(request, 'این تیکت قبلاً بسته شده است.')
        return redirect('accounts:support_panel_ticket_detail', ticket_id=ticket.id)
    
    if action == 'reopen':
        if ticket.status == 'closed':
            ticket.reopen()
            messages.success(request, f'✅ تیکت #{ticket.id} با موفقیت باز شد.')
        else:
            messages.info(request, 'این تیکت در حال حاضر باز است.')
        return redirect('accounts:support_panel_ticket_detail', ticket_id=ticket.id)
    
    if request.method == 'POST':
        form = SupportMessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.ticket = ticket
            msg.sender = request.user
            msg.is_staff = True
            msg.save()
            
            # ===== به‌روزرسانی وضعیت بر اساس آخرین پیام =====
            ticket.update_status_based_on_last_message()
            
            messages.success(request, '✅ پاسخ ارسال شد.')
            return redirect('accounts:support_panel_ticket_detail', ticket_id=ticket.id)
    else:
        form = SupportMessageForm()
    
    messages_qs = ticket.messages.select_related('sender').order_by('created')
    return render(request, 'accounts/support_panel_ticket_detail.html', {
        'ticket': ticket,
        'messages': messages_qs,
        'form': form,
        'is_support_panel': True,
    })


# ============================================================
# 🏆 وارت کوین - خرید و مدیریت
# ============================================================

@login_required
@require_http_methods(["GET", "POST"])
@csrf_protect
def buy_wart_coins_view(request):
    settings_obj = WartCoinSettings.load()
    discounts = BulkDiscount.objects.filter(is_active=True).order_by('order', 'min_amount')
    
    if request.method == 'POST':
        try:
            coin_amount = int(request.POST.get('coin_amount', 0))
            if coin_amount < 1:
                raise ValueError('مقدار نامعتبر است.')
            
            total_price = settings_obj.get_price_for_amount(coin_amount)
            
            discount = BulkDiscount.objects.filter(
                min_amount__lte=coin_amount,
                is_active=True
            ).order_by('-min_amount').first()
            price_per_coin = discount.price_per_coin if discount else settings_obj.base_price_per_coin
            
            purchase = WartCoinPurchase.objects.create(
                user=request.user,
                coin_amount=coin_amount,
                price_per_coin=price_per_coin,
                total_price=total_price,
                transaction_id=str(uuid.uuid4())
            )
            
            return redirect('orders:payment_wart_coin', purchase_id=purchase.id)
        except ValueError:
            messages.error(request, 'مقدار نامعتبر است.')
        except Exception as e:
            messages.error(request, f'خطا: {str(e)}')
    
    return render(request, 'accounts/buy_wart_coins.html', {
        'settings': settings_obj,
        'discounts': discounts,
    })


@login_required
@require_http_methods(["POST"])
@csrf_protect
def get_wart_coin_price_api(request):
    try:
        coin_amount = int(request.POST.get('coin_amount', 0))
        if coin_amount < 1:
            return JsonResponse({'error': 'مقدار نامعتبر است.'}, status=400)
        
        settings_obj = WartCoinSettings.load()
        total_price = settings_obj.get_price_for_amount(coin_amount)
        
        discount = BulkDiscount.objects.filter(
            min_amount__lte=coin_amount,
            is_active=True
        ).order_by('-min_amount').first()
        price_per_coin = discount.price_per_coin if discount else settings_obj.base_price_per_coin
        
        return JsonResponse({
            'total_price': float(total_price),
            'price_per_coin': float(price_per_coin),
            'formatted_total_price': f'{total_price:,.0f}',
        })
    except (ValueError, TypeError):
        return JsonResponse({'error': 'مقدار نامعتبر است.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def wart_coin_balance_api(request):
    wallet, created = WartCoin.objects.get_or_create(user=request.user)
    return JsonResponse({
        'balance': float(wallet.balance),
        'formatted_balance': f'{wallet.balance:,.2f}',
    })


# ============================================================
# 📊 جدول رهبری وارت کوین
# ============================================================

def wart_coin_leaderboard(request):
    from decimal import InvalidOperation, Decimal
    from django.db import connection
    
    top_wallets = []
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, balance 
                FROM accounts_wartcoin 
                WHERE balance IS NOT NULL 
                ORDER BY CAST(balance AS REAL) DESC 
                LIMIT 100
            """)
            top_wallet_data = cursor.fetchall()
        
        for wallet_id, balance_value in top_wallet_data:
            try:
                if balance_value is not None and balance_value != '':
                    try:
                        Decimal(str(balance_value))
                    except (InvalidOperation, ValueError, TypeError):
                        try:
                            with connection.cursor() as cursor:
                                cursor.execute(
                                    "UPDATE accounts_wartcoin SET balance = 0.00 WHERE id = ?",
                                    [wallet_id]
                                )
                                connection.commit()
                        except Exception:
                            pass
                        continue
                
                wallet = WartCoin.objects.select_related('user', 'user__profile').get(pk=wallet_id)
                _ = wallet.balance
                top_wallets.append(wallet)
            except (InvalidOperation, ValueError, TypeError, Exception):
                continue
        
        top_wallets.sort(key=lambda w: w.balance, reverse=True)
        
    except Exception:
        top_wallets = []
    
    user_rank = None
    user_wallet = None
    if request.user.is_authenticated:
        try:
            user_wallet, created = WartCoin.objects.get_or_create(user=request.user)
            if user_wallet:
                try:
                    _ = user_wallet.balance
                    try:
                        user_rank = WartCoin.objects.filter(balance__gt=user_wallet.balance).count() + 1
                    except Exception:
                        user_rank = sum(1 for w in top_wallets if w.balance > user_wallet.balance) + 1
                except (InvalidOperation, ValueError, TypeError):
                    try:
                        user_wallet.balance = Decimal('0.00')
                        user_wallet.save(update_fields=['balance'])
                        user_rank = len(top_wallets) + 1
                    except Exception:
                        pass
        except Exception:
            pass
    
    leaderboard_data = []
    for index, wallet in enumerate(top_wallets, start=1):
        try:
            balance = wallet.balance
            leaderboard_data.append({
                'rank': index,
                'user': wallet.user,
                'balance': balance,
                'username': wallet.user.get_full_name() or wallet.user.username,
                'minecraft_username': wallet.user.profile.minecraft_username if hasattr(wallet.user, 'profile') and wallet.user.profile else None,
            })
        except (InvalidOperation, ValueError, TypeError):
            continue
    
    return render(request, 'accounts/wart_coin_leaderboard.html', {
        'leaderboard': leaderboard_data,
        'user_rank': user_rank,
        'user_wallet': user_wallet,
    })


# ============================================================
# ℹ️ اطلاعات سایت
# ============================================================

def more_info_view(request):
    site_info = SiteInfo.load()
    return render(request, 'accounts/more_info.html', {'site_info': site_info})


def admin_info_view(request):
    site_info = SiteInfo.load()
    admins = User.objects.filter(is_staff=True).select_related('profile')
    return render(request, 'accounts/admin_info.html', {
        'site_info': site_info,
        'admins': admins,
    })


# ============================================================
# ✅ تایید ایمیل با لینک (برای سازگاری)
# ============================================================

def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, '✅ ایمیل تایید شد!')
        return render(request, 'accounts/verify_email_success.html', {'success': True})
    else:
        messages.error(request, '❌ لینک نامعتبر است.')
        return render(request, 'accounts/verify_email_success.html', {'success': False})