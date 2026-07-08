from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.core.exceptions import ValidationError
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.db import connection, transaction
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import (
    SupportTicket, SupportMessage,
    WartCoin, WartCoinPurchase, WartCoinTransaction,
    WartCoinSettings, BulkDiscount, SiteInfo, UserProfile
)


# ---------- Helpers ----------
def safe_decimal(value, default=Decimal('0.00')):
    """
    سعی می‌کند مقدار را به Decimal تبدیل کند؛ در صورت خطا مقدار پیش‌فرض را برمی‌گرداند.
    """
    try:
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return default


def find_invalid_wartcoin_ids():
    invalid_ids = []
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, balance FROM accounts_wartcoin")
        for record_id, balance_value in cursor.fetchall():
            if balance_value is None or balance_value == '':
                continue
            try:
                Decimal(str(balance_value)).quantize(Decimal('0.01'))
            except Exception:
                invalid_ids.append(record_id)
    return invalid_ids


def find_invalid_transaction_ids_for_wallet(wallet_id):
    invalid_ids = []
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, amount, balance_after FROM accounts_wartcointransaction WHERE wallet_id = %s",
            [wallet_id]
        )
        for trans_id, amount_value, balance_after_value in cursor.fetchall():
            needs_fix = False
            if amount_value is not None and amount_value != '':
                try:
                    Decimal(str(amount_value))
                except Exception:
                    needs_fix = True
            if balance_after_value is not None and balance_after_value != '':
                try:
                    Decimal(str(balance_after_value))
                except Exception:
                    needs_fix = True
            if needs_fix:
                invalid_ids.append(trans_id)
    return invalid_ids


# ---------- Support Admins ----------
class SupportMessageInline(admin.TabularInline):
    model = SupportMessage
    extra = 0
    readonly_fields = ['sender', 'is_staff', 'message', 'created']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    """مدیریت تیکت‌های پشتیبانی - فقط وضعیت‌های اصلی"""
    
    list_display = [
        'id',
        'subject_display',
        'user_display',
        'status_badge',
        'assigned_admins_display',
        'created_display',
        'updated_display',
        'view_ticket_link'
    ]
    
    # فیلتر فقط با وضعیت‌های اصلی
    list_filter = [
        ('status', admin.ChoicesFieldListFilter),  # نمایش فقط انتخاب‌های موجود
    ]
    
    search_fields = [
        'subject',
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name'
    ]
    
    readonly_fields = ['id', 'created', 'updated', 'messages_display']
    filter_horizontal = ['assigned_admins']
    inlines = [SupportMessageInline]
    
    # اکشن‌های گروهی ساده
    actions = [
        'mark_as_answered',
        'mark_as_closed',
        'mark_as_reopened',
        'mark_as_pending_user',
        'mark_as_pending_admin'
    ]

    fieldsets = (
        ('اطلاعات تیکت', {
            'fields': ('id', 'user', 'subject', 'status')
        }),
        ('ادمین‌های اختصاص‌یافته', {
            'fields': ('assigned_admins',),
            'description': 'کاربرانی که می‌توانند به این تیکت پاسخ دهند را انتخاب کنید.'
        }),
        ('تاریخ‌ها', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
        ('پیام‌های تیکت', {
            'fields': ('messages_display',),
            'classes': ('collapse',)
        }),
    )

    # ===== نمایش‌ها =====
    def subject_display(self, obj):
        url = reverse('admin:accounts_supportticket_change', args=[obj.pk])
        return format_html('<a href="{}">{}</a>', url, obj.subject[:50])
    subject_display.short_description = 'موضوع'
    subject_display.admin_order_field = 'subject'

    def user_display(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        full_name = obj.user.get_full_name() or obj.user.username
        return format_html('<a href="{}">{}</a>', url, full_name)
    user_display.short_description = 'کاربر'
    user_display.admin_order_field = 'user__username'

    def status_badge(self, obj):
        """نمایش وضعیت با رنگ مناسب"""
        status_colors = {
            'new': '#17a2b8',
            'pending_user': '#ffc107',
            'pending_admin': '#fd7e14',
            'answered': '#28a745',
            'closed': '#6c757d',
            'reopened': '#20c997',
        }
        status_labels = dict(SupportTicket.STATUS_CHOICES)
        color = status_colors.get(obj.status, '#6c757d')
        label = status_labels.get(obj.status, obj.status)
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 600;">{}</span>',
            color,
            'white' if obj.status != 'pending_user' else '#212529',
            label
        )
    status_badge.short_description = 'وضعیت'
    status_badge.admin_order_field = 'status'

    def assigned_admins_display(self, obj):
        admins = obj.assigned_admins.all()
        if not admins.exists():
            return mark_safe('<span style="color: #999;">هیچ ادمینی اختصاص داده نشده</span>')
        admin_links = []
        for admin_user in admins:
            url = reverse('admin:auth_user_change', args=[admin_user.pk])
            name = admin_user.get_full_name() or admin_user.username
            admin_links.append(format_html('<a href="{}">{}</a>', url, name))
        return mark_safe(', '.join(admin_links))
    assigned_admins_display.short_description = 'ادمین‌ها'

    def created_display(self, obj):
        return obj.created.strftime('%Y/%m/%d %H:%M')
    created_display.short_description = 'تاریخ ایجاد'
    created_display.admin_order_field = 'created'

    def updated_display(self, obj):
        return obj.updated.strftime('%Y/%m/%d %H:%M')
    updated_display.short_description = 'آخرین بروزرسانی'
    updated_display.admin_order_field = 'updated'

    def messages_display(self, obj):
        messages_qs = obj.messages.all()[:5]
        if not messages_qs.exists():
            return 'هنوز پیامی ارسال نشده است.'
        
        html = '<div style="max-height: 300px; overflow-y: auto;">'
        for msg in messages_qs:
            sender_name = msg.sender.get_full_name() if msg.sender else 'کاربر حذف شده'
            staff_badge = ' <span style="background: #007bff; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">پشتیبانی</span>' if msg.is_staff else ''
            html += format_html(
                '<div style="margin-bottom: 10px; padding: 8px; background: #f5f5f5; border-radius: 4px;">'
                '<strong>{}{}</strong> - <small>{}</small><br>'
                '<div style="margin-top: 5px;">{}</div>'
                '</div>',
                sender_name, staff_badge, msg.created.strftime('%Y/%m/%d %H:%M'), msg.message[:200]
            )
        if obj.messages.count() > 5:
            html += f'<p><small>و {obj.messages.count() - 5} پیام دیگر...</small></p>'
        html += '</div>'
        return mark_safe(html)
    messages_display.short_description = 'پیام‌های تیکت'

    def view_ticket_link(self, obj):
        if obj.pk:
            url = reverse('accounts:support_panel_ticket_detail', args=[obj.pk])
            return format_html('<a href="{}" target="_blank" style="background: #28a745; color: white; padding: 3px 12px; border-radius: 4px; text-decoration: none; font-size: 12px;">🔍 مشاهده</a>', url)
        return '-'
    view_ticket_link.short_description = 'عملیات'

    # ===== اکشن‌های گروهی =====
    def mark_as_answered(self, request, queryset):
        updated = queryset.update(status='answered')
        self.message_user(request, f'{updated} تیکت به وضعیت "پاسخ داده شده" تغییر یافت.')
    mark_as_answered.short_description = '✅ تغییر وضعیت به "پاسخ داده شده"'

    def mark_as_closed(self, request, queryset):
        updated = queryset.update(status='closed')
        self.message_user(request, f'{updated} تیکت به وضعیت "بسته شده" تغییر یافت.')
    mark_as_closed.short_description = '🔒 تغییر وضعیت به "بسته شده"'

    def mark_as_reopened(self, request, queryset):
        updated = queryset.update(status='reopened')
        self.message_user(request, f'{updated} تیکت به وضعیت "دوباره باز شده" تغییر یافت.')
    mark_as_reopened.short_description = '🔓 تغییر وضعیت به "دوباره باز شده"'

    def mark_as_pending_user(self, request, queryset):
        updated = queryset.update(status='pending_user')
        self.message_user(request, f'{updated} تیکت به وضعیت "منتظر پاسخ کاربر" تغییر یافت.')
    mark_as_pending_user.short_description = '⏳ تغییر وضعیت به "منتظر پاسخ کاربر"'

    def mark_as_pending_admin(self, request, queryset):
        updated = queryset.update(status='pending_admin')
        self.message_user(request, f'{updated} تیکت به وضعیت "منتظر پاسخ ادمین" تغییر یافت.')
    mark_as_pending_admin.short_description = '⏳ تغییر وضعیت به "منتظر پاسخ ادمین"'

    # ===== جلوگیری از حذف وضعیت‌های اضافی =====
    def get_list_filter(self, request):
        return [
            ('status', admin.ChoicesFieldListFilter),
        ]


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'ticket_link', 'sender_display', 'is_staff_badge', 'message_preview', 'created_display']
    list_filter = ['is_staff', 'created', 'ticket__status']
    search_fields = ['message', 'ticket__subject', 'sender__username', 'sender__email']
    readonly_fields = ['ticket', 'sender', 'is_staff', 'message', 'created']

    fieldsets = (
        ('اطلاعات پیام', {
            'fields': ('ticket', 'sender', 'is_staff', 'message', 'created')
        }),
    )

    def ticket_link(self, obj):
        url = reverse('admin:accounts_supportticket_change', args=[obj.ticket.pk])
        return format_html('<a href="{}">تیکت #{}</a>', url, obj.ticket.id)
    ticket_link.short_description = 'تیکت'
    ticket_link.admin_order_field = 'ticket__id'

    def sender_display(self, obj):
        if obj.sender:
            url = reverse('admin:auth_user_change', args=[obj.sender.pk])
            name = obj.sender.get_full_name() or obj.sender.username
            return format_html('<a href="{}">{}</a>', url, name)
        return 'کاربر حذف شده'
    sender_display.short_description = 'فرستنده'
    sender_display.admin_order_field = 'sender__username'

    def is_staff_badge(self, obj):
        if obj.is_staff:
            return format_html(
                '<span style="background-color: #007bff; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">پشتیبانی</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">کاربر</span>'
        )
    is_staff_badge.short_description = 'نوع'

    def message_preview(self, obj):
        preview = obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
        return preview
    message_preview.short_description = 'متن پیام'

    def created_display(self, obj):
        return obj.created.strftime('%Y/%m/%d %H:%M')
    created_display.short_description = 'تاریخ ارسال'
    created_display.admin_order_field = 'created'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# ---------- Custom UserAdmin ----------
class CustomUserAdmin(BaseUserAdmin):
    def save_model(self, request, obj, form, change):
        if obj.email:
            existing_user = User.objects.filter(email=obj.email).exclude(pk=obj.pk if obj.pk else 0).first()
            if existing_user:
                messages.error(
                    request,
                    f'❌ خطا: این ایمیل ({obj.email}) قبلاً توسط کاربر "{existing_user.username}" استفاده شده است. '
                    'لطفاً یک ایمیل دیگر انتخاب کنید.'
                )
                raise ValidationError(
                    f'این ایمیل ({obj.email}) قبلاً توسط کاربر "{existing_user.username}" استفاده شده است.'
                )

        if obj.is_superuser and not obj.email:
            messages.warning(
                request,
                '⚠️ توجه: برای superuser بهتر است یک ایمیل معتبر تنظیم شود.'
            )

        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return super().has_delete_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return super().has_change_permission(request, obj)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if request.user.is_superuser:
            if 'delete_selected' not in actions:
                from django.contrib.admin.actions import delete_selected
                actions['delete_selected'] = (delete_selected, 'delete_selected', 'حذف کاربران انتخاب شده')
        return actions

    def delete_model(self, request, obj):
        try:
            if hasattr(obj, 'wart_coin'):
                obj.wart_coin.delete()
        except Exception:
            pass
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        user_ids = list(queryset.values_list('id', flat=True))
        WartCoin.objects.filter(user_id__in=user_ids).delete()
        super().delete_queryset(request, queryset)

    def get_deleted_objects(self, objs, request):
        if request.user.is_superuser:
            from django.contrib.admin.utils import get_deleted_objects
            from django.contrib.admin import site

            deleted_objects, model_count, perms_needed, protected = get_deleted_objects(objs, request, site)

            protected = [
                obj for obj in protected
                if not hasattr(obj, '_meta') or obj._meta.model_name != 'wartcoin'
            ]

            return deleted_objects, model_count, perms_needed, protected
        return super().get_deleted_objects(objs, request)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# ---------- Wart Coin Admin ----------
@admin.register(WartCoinSettings)
class WartCoinSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not WartCoinSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    list_display = ['base_price_per_coin', 'updated']
    fieldsets = (
        ('تنظیمات قیمت', {
            'fields': ('base_price_per_coin',),
            'description': '💰 قیمت پایه هر واحد وارت کوین به تومان. این قیمت زمانی استفاده می‌شود که تخفیف خرید عمده تنظیم نشده باشد.'
        }),
    )
    readonly_fields = ['updated']

    def get_queryset(self, request):
        WartCoinSettings.load()
        return super().get_queryset(request).filter(pk=1)


@admin.register(BulkDiscount)
class BulkDiscountAdmin(admin.ModelAdmin):
    list_display = ['min_amount', 'price_per_coin', 'total_price_example', 'is_active', 'order']
    list_filter = ['is_active']
    list_editable = ['is_active', 'order']
    ordering = ['order', 'min_amount']
    search_fields = ['min_amount']

    fieldsets = (
        ('اطلاعات تخفیف', {
            'fields': ('min_amount', 'price_per_coin', 'is_active', 'order'),
            'description': '💡 حداقل مقدار وارت کوین برای دریافت این تخفیف و قیمت هر واحد'
        }),
    )

    def total_price_example(self, obj):
        example_amount = obj.min_amount
        total = safe_decimal(obj.price_per_coin) * Decimal(str(example_amount))
        return format_html(
            '<span style="color: #4CAF50; font-weight: bold;">{} تومان</span><br>'
            '<small style="color: #999;">({} WC × {} تومان)</small>',
            f"{total:,.0f}", example_amount, f"{safe_decimal(obj.price_per_coin):,.0f}"
        )
    total_price_example.short_description = 'قیمت کل (مثال)'


class WartCoinTransactionInline(admin.TabularInline):
    model = WartCoinTransaction
    extra = 0
    readonly_fields = ['amount', 'transaction_type', 'reason', 'balance_after', 'related_order', 'created']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(WartCoin)
class WartCoinAdmin(admin.ModelAdmin):
    list_display = ['user_link', 'balance_display', 'transactions_count', 'last_transaction', 'wallet_actions']
    list_filter = ['updated', 'created']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['user', 'created', 'updated', 'balance_history']
    actions = ['add_coins_action', 'deduct_coins_action', 'set_balance_action']
    fieldsets = (
        ('اطلاعات کیف پول', {
            'fields': ('user', 'balance', 'created', 'updated'),
            'description': '💰 superuser می‌تواند موجودی وارت کوین کاربران را تغییر دهد. تغییرات به صورت خودکار در تاریخچه ثبت می‌شوند.'
        }),
        ('تاریخچه تراکنش‌ها', {
            'fields': ('balance_history',),
            'classes': ('collapse',)
        }),
    )
    inlines = [WartCoinTransactionInline]

    def get_queryset(self, request):
        try:
            return super().get_queryset(request).select_related('user', 'user__profile')
        except Exception:
            try:
                invalid_ids = find_invalid_wartcoin_ids()
                if invalid_ids:
                    WartCoin.objects.filter(id__in=invalid_ids).update(balance=Decimal('0.00'))
                return super().get_queryset(request).select_related('user', 'user__profile')
            except Exception:
                return WartCoin.objects.none()

    def changelist_view(self, request, extra_context=None):
        if not hasattr(request, '_wartcoin_changelist_fixed'):
            try:
                invalid_ids = find_invalid_wartcoin_ids()
                if invalid_ids:
                    WartCoin.objects.filter(id__in=invalid_ids).update(balance=Decimal('0.00'))
                    messages.success(request, f'{len(invalid_ids)} رکورد نامعتبر اصلاح شد. لطفا صفحه را رفرش کنید.')
            except Exception:
                messages.warning(request, 'تلاش برای اصلاح رکوردهای نامعتبر انجام شد اما کامل نشد.')
            finally:
                request._wartcoin_changelist_fixed = True

        try:
            return super().changelist_view(request, extra_context)
        except InvalidOperation:
            messages.error(request, 'خطا در تبدیل مقادیر عددی. لطفا اسکریپت تعمیر دیتابیس را اجرا کنید.')
            return redirect('admin:accounts_wartcoin_changelist')

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:object_id>/change-balance/',
                self.admin_site.admin_view(self.change_balance_view),
                name='accounts_wartcoin_change_balance',
            ),
        ]
        return custom_urls + urls

    def change_balance_view(self, request, object_id):
        wallet = get_object_or_404(WartCoin, pk=object_id)

        if not request.user.is_superuser:
            messages.error(request, 'فقط superuser می‌تواند موجودی را تغییر دهد.')
            return redirect('admin:accounts_wartcoin_changelist')

        if request.method == 'POST':
            new_balance_str = request.POST.get('balance', '0')
            reason = request.POST.get('reason', 'تغییر دستی موجودی توسط ادمین')

            try:
                new_balance = safe_decimal(new_balance_str)
                if new_balance < 0:
                    messages.error(request, 'موجودی نمی‌تواند منفی باشد.')
                else:
                    old_balance = safe_decimal(wallet.balance)
                    if old_balance != new_balance:
                        amount = new_balance - old_balance

                        wallet.balance = new_balance
                        wallet.save(update_fields=['balance', 'updated'])

                        WartCoinTransaction.objects.create(
                            wallet=wallet,
                            amount=amount,
                            transaction_type='manual',
                            reason=f'{reason} ({request.user.username})',
                            balance_after=wallet.balance
                        )
                        messages.success(request, f'موجودی {wallet.user.username} از {old_balance} به {wallet.balance} وارت کوین تغییر کرد.')
                    else:
                        messages.info(request, 'موجودی تغییر نکرد.')

                    return redirect('admin:accounts_wartcoin_changelist')
            except (ValueError, TypeError):
                messages.error(request, 'مقدار نامعتبر است.')

        try:
            invalid_transaction_ids = find_invalid_transaction_ids_for_wallet(wallet.pk)
            if invalid_transaction_ids:
                WartCoinTransaction.objects.filter(id__in=invalid_transaction_ids).update(amount=Decimal('0.00'), balance_after=Decimal('0.00'))
        except Exception:
            pass

        safe_transactions = []
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id, amount, transaction_type, reason, created, balance_after 
                    FROM accounts_wartcointransaction 
                    WHERE wallet_id = %s 
                    ORDER BY created DESC 
                    LIMIT 5
                """, [wallet.pk])
                for row in cursor.fetchall():
                    trans_id, amount_val, trans_type, reason_text, created_val, balance_after_val = row
                    try:
                        amount_decimal = safe_decimal(amount_val)
                        balance_after_decimal = safe_decimal(balance_after_val)
                        if created_val:
                            if isinstance(created_val, str):
                                formatted_date = created_val[:16].replace('T', ' ')
                            else:
                                try:
                                    formatted_date = created_val.strftime('%Y/%m/%d %H:%M')
                                except Exception:
                                    formatted_date = str(created_val)[:16]
                        else:
                            formatted_date = '-'

                        safe_transactions.append({
                            'id': trans_id,
                            'amount': float(amount_decimal),
                            'transaction_type': trans_type or '',
                            'reason': reason_text or '',
                            'created': formatted_date or '-',
                            'balance_after': float(balance_after_decimal),
                        })
                    except Exception:
                        continue
        except Exception:
            pass

        context = {
            **self.admin_site.each_context(request),
            'title': f'تغییر موجودی - {wallet.user.username}',
            'wallet': wallet,
            'safe_transactions': safe_transactions,
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request, wallet),
            'has_change_permission': self.has_change_permission(request, wallet),
        }

        return TemplateResponse(request, 'admin/accounts/wartcoin/change_balance.html', context)

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        readonly.append('balance')
        return readonly

    def has_change_permission(self, request, obj=None):
        try:
            if request.resolver_match and getattr(request.resolver_match, 'url_name', '') and 'change_balance' in request.resolver_match.url_name:
                return request.user.is_superuser
        except Exception:
            pass
        return super().has_change_permission(request, obj)

    def save_model(self, request, obj, form, change):
        if change and obj.pk:
            old_obj = WartCoin.objects.get(pk=obj.pk)
            old_balance = safe_decimal(old_obj.balance)
            new_balance = safe_decimal(obj.balance)

            if old_balance != new_balance:
                amount = new_balance - old_balance
                WartCoinTransaction.objects.create(
                    wallet=obj,
                    amount=amount,
                    transaction_type='manual',
                    reason=f'تغییر دستی موجودی توسط ادمین ({request.user.username})',
                    balance_after=new_balance
                )

        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return super().has_delete_permission(request, obj)

    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        name = obj.user.get_full_name() or obj.user.username
        return format_html('<a href="{}">{}</a>', url, name)
    user_link.short_description = 'کاربر'

    def balance_display(self, obj):
        try:
            if obj.balance is None:
                return '-'
            balance_value = safe_decimal(obj.balance)
            return format_html(
                '<span style="font-size: 1.2rem; font-weight: bold; color: #4CAF50;">{} WC</span>',
                f"{balance_value:,.2f}"
            )
        except (ValueError, TypeError, AttributeError):
            return '-'
    balance_display.short_description = 'موجودی'

    def transactions_count(self, obj):
        count = obj.transactions.count()
        return format_html(
            '<span style="background: #2196F3; color: white; padding: 3px 10px; border-radius: 15px;">{} تراکنش</span>',
            count
        )
    transactions_count.short_description = 'تعداد تراکنش‌ها'

    def last_transaction(self, obj):
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT created FROM accounts_wartcointransaction WHERE wallet_id = %s ORDER BY created DESC LIMIT 1",
                    [obj.pk]
                )
                result = cursor.fetchone()
                if result and result[0]:
                    val = result[0]
                    if isinstance(val, str):
                        return val[:16].replace('T', ' ')
                    try:
                        return val.strftime('%Y/%m/%d %H:%M')
                    except Exception:
                        return str(val)[:16]
            return '-'
        except Exception:
            try:
                last = obj.transactions.order_by('-created').first()
                if last:
                    return last.created.strftime('%Y/%m/%d %H:%M')
            except Exception:
                pass
            return '-'
    last_transaction.short_description = 'آخرین تراکنش'

    def wallet_actions(self, obj):
        if not obj.pk:
            return '-'
        url = reverse('admin:accounts_wartcoin_change_balance', args=[obj.pk])
        return format_html(
            '<a href="{}" class="button" style="background: #4CAF50; color: white; padding: 5px 15px; border-radius: 5px; text-decoration: none; font-weight: bold; display: inline-block;">💰 تغییر موجودی</a>',
            url
        )
    wallet_actions.short_description = 'عملیات'

    def balance_history(self, obj):
        transactions = obj.transactions.order_by('-created')[:10]
        if not transactions.exists():
            return 'هنوز تراکنشی ثبت نشده است.'

        html = '<div style="max-height: 400px; overflow-y: auto;">'
        for txn in transactions:
            try:
                amount_decimal = safe_decimal(txn.amount)
                sign = '+' if amount_decimal >= 0 else ''
                amount_value = amount_decimal
                color = '#4CAF50' if amount_value >= 0 else '#f44336'
                balance_after_value = safe_decimal(txn.balance_after)
                html += format_html(
                    '<div style="padding: 8px; margin-bottom: 5px; background: #f5f5f5; border-radius: 5px; border-right: 3px solid {};">'
                    '<strong style="color: {};">{}{} WC</strong> - {} - <small>{}</small><br>'
                    '<small style="color: #999;">موجودی بعد: {} WC</small>'
                    '</div>',
                    color, color, sign, f"{amount_value:,.2f}", txn.get_transaction_type_display(),
                    txn.created.strftime('%Y/%m/%d %H:%M'), f"{balance_after_value:,.2f}"
                )
            except (ValueError, TypeError, AttributeError):
                continue
        html += '</div>'
        return mark_safe(html)
    balance_history.short_description = 'تاریخچه'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

    def add_coins_action(self, request, queryset):
        if not request.user.is_superuser:
            self.message_user(request, 'فقط superuser می‌تواند این عملیات را انجام دهد.', level=messages.ERROR)
            return

        amount = Decimal('100')
        reason = 'افزودن دستی توسط ادمین'

        count = 0
        for wallet in queryset:
            try:
                wallet.add_coins(
                    amount=amount,
                    reason=f'{reason} ({request.user.username})',
                    transaction_type='manual'
                )
                count += 1
            except Exception:
                continue

        self.message_user(request, f'به {count} کیف پول، {amount} وارت کوین اضافه شد. برای تغییر مقدار دقیق از صفحه ویرایش استفاده کنید.', level=messages.SUCCESS)
    add_coins_action.short_description = '➕ افزودن 100 وارت کوین (برای تغییر دقیق از صفحه ویرایش استفاده کنید)'

    def deduct_coins_action(self, request, queryset):
        if not request.user.is_superuser:
            self.message_user(request, 'فقط superuser می‌تواند این عملیات را انجام دهد.', level=messages.ERROR)
            return

        amount = Decimal('50')
        reason = 'کسر دستی توسط ادمین'

        count = 0
        failed = 0
        for wallet in queryset:
            try:
                wallet.deduct_coins(
                    amount=amount,
                    reason=f'{reason} ({request.user.username})',
                    transaction_type='manual'
                )
                count += 1
            except ValueError:
                failed += 1
            except Exception:
                failed += 1

        if count > 0:
            self.message_user(request, f'از {count} کیف پول، {amount} وارت کوین کسر شد.', level=messages.SUCCESS)
        if failed > 0:
            self.message_user(request, f'{failed} کیف پول به دلیل موجودی ناکافی یا خطا تغییر نکرد.', level=messages.WARNING)
    deduct_coins_action.short_description = '➖ کسر 50 وارت کوین (برای تغییر دقیق از صفحه ویرایش استفاده کنید)'

    def set_balance_action(self, request, queryset):
        if not request.user.is_superuser:
            self.message_user(request, 'فقط superuser می‌تواند این عملیات را انجام دهد.', level=messages.ERROR)
            return

        new_balance = Decimal('0')
        reason = 'تنظیم دستی موجودی توسط ادمین'

        count = 0
        for wallet in queryset:
            try:
                old_balance = safe_decimal(wallet.balance)
                if old_balance != new_balance:
                    amount = new_balance - old_balance

                    wallet.balance = new_balance
                    wallet.save(update_fields=['balance', 'updated'])

                    WartCoinTransaction.objects.create(
                        wallet=wallet,
                        amount=amount,
                        transaction_type='manual',
                        reason=f'{reason} ({request.user.username})',
                        balance_after=wallet.balance
                    )
                    count += 1
            except Exception:
                continue

        self.message_user(request, f'موجودی {count} کیف پول به {new_balance} وارت کوین تنظیم شد. برای تنظیم مقدار دقیق از صفحه ویرایش استفاده کنید.', level=messages.SUCCESS)
    set_balance_action.short_description = '⚙️ تنظیم موجودی به صفر (برای تغییر دقیق از صفحه ویرایش استفاده کنید)'

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.user.is_superuser:
            for action in ['add_coins_action', 'deduct_coins_action', 'set_balance_action']:
                if action in actions:
                    del actions[action]
        return actions


@admin.register(WartCoinPurchase)
class WartCoinPurchaseAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user_link', 'coin_amount', 'price_per_coin', 'total_price_display',
        'payment_status_badge', 'transaction_id', 'created_display'
    ]
    list_filter = ['payment_status', 'created']
    search_fields = ['user__username', 'user__email', 'payment_id', 'transaction_id']
    readonly_fields = [
        'user', 'coin_amount', 'price_per_coin', 'total_price',
        'payment_id', 'transaction_id', 'created', 'updated'
    ]
    date_hierarchy = 'created'

    fieldsets = (
        ('اطلاعات خرید', {
            'fields': ('user', 'coin_amount', 'price_per_coin', 'total_price')
        }),
        ('وضعیت پرداخت', {
            'fields': ('payment_status', 'payment_id', 'transaction_id')
        }),
        ('تاریخ‌ها', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )

    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        name = obj.user.get_full_name() or obj.user.username
        return format_html('<a href="{}">{}</a>', url, name)
    user_link.short_description = 'کاربر'

    def total_price_display(self, obj):
        try:
            if obj.total_price is None:
                return '-'
            total = safe_decimal(obj.total_price)
            return format_html(
                '<span style="font-weight: bold; color: #4CAF50;">{} تومان</span>',
                f"{total:,.0f}"
            )
        except (ValueError, TypeError, AttributeError):
            return '-'
    total_price_display.short_description = 'قیمت کل'

    def payment_status_badge(self, obj):
        colors = {
            'pending': '#FFC107',
            'completed': '#4CAF50',
            'failed': '#f44336',
            'cancelled': '#9E9E9E'
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 15px; font-weight: bold;">{}</span>',
            colors.get(obj.payment_status, '#999'), obj.get_payment_status_display()
        )
    payment_status_badge.short_description = 'وضعیت پرداخت'

    def created_display(self, obj):
        return obj.created.strftime('%Y/%m/%d %H:%M')
    created_display.short_description = 'تاریخ'

    def has_add_permission(self, request):
        return False


@admin.register(WartCoinTransaction)
class WartCoinTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'wallet_link', 'amount_display', 'transaction_type_badge',
        'reason', 'balance_after_display', 'related_order_link', 'created_display'
    ]
    list_filter = ['transaction_type', 'created']
    search_fields = ['wallet__user__username', 'wallet__user__email', 'reason', 'transaction_id']
    readonly_fields = [
        'wallet', 'amount', 'transaction_type', 'reason',
        'balance_after', 'related_order', 'created'
    ]
    date_hierarchy = 'created'

    def wallet_link(self, obj):
        url = reverse('admin:accounts_wartcoin_change', args=[obj.wallet.pk])
        name = obj.wallet.user.get_full_name() or obj.wallet.user.username
        return format_html('<a href="{}">{}</a>', url, name)
    wallet_link.short_description = 'کاربر'

    def amount_display(self, obj):
        try:
            amount_decimal = safe_decimal(obj.amount)
            sign = '+' if amount_decimal >= 0 else ''
            color = '#4CAF50' if amount_decimal >= 0 else '#f44336'
            return format_html(
                '<span style="font-weight: bold; color: {}; font-size: 1.1rem;">{}{} WC</span>',
                color, sign, f"{amount_decimal:,.2f}"
            )
        except Exception:
            return '-'
    amount_display.short_description = 'مقدار'

    def transaction_type_badge(self, obj):
        colors = {
            'purchase': '#4CAF50',
            'spend': '#f44336',
            'manual': '#2196F3',
            'refund': '#FFC107'
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 15px;">{}</span>',
            colors.get(obj.transaction_type, '#999'), obj.get_transaction_type_display()
        )
    transaction_type_badge.short_description = 'نوع'

    def balance_after_display(self, obj):
        try:
            if obj.balance_after is None:
                return '-'
            balance_value = safe_decimal(obj.balance_after)
            return format_html('<span style="font-weight: bold;">{} WC</span>', f"{balance_value:,.2f}")
        except (ValueError, TypeError, AttributeError):
            return '-'
    balance_after_display.short_description = 'موجودی بعد'

    def related_order_link(self, obj):
        if obj.related_order:
            url = reverse('admin:orders_order_change', args=[obj.related_order.pk])
            return format_html('<a href="{}">سفارش #{}</a>', url, obj.related_order.id)
        return '-'
    related_order_link.short_description = 'سفارش مرتبط'

    def created_display(self, obj):
        return obj.created.strftime('%Y/%m/%d %H:%M')
    created_display.short_description = 'تاریخ'

    def has_add_permission(self, request):
        return False


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user_link', 'minecraft_username', 'created', 'updated']
    list_filter = ['created', 'updated']
    search_fields = ['user__username', 'user__email', 'minecraft_username']
    readonly_fields = ['user', 'created', 'updated']

    fieldsets = (
        ('اطلاعات کاربر', {
            'fields': ('user',)
        }),
        ('اطلاعات ماینکرفت', {
            'fields': ('minecraft_username',)
        }),
        ('تاریخ‌ها', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )

    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        name = obj.user.get_full_name() or obj.user.username
        return format_html('<a href="{}">{}</a>', url, name)
    user_link.short_description = 'کاربر'

    def has_add_permission(self, request):
        return False


@admin.register(SiteInfo)
class SiteInfoAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SiteInfo.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    list_display = ['discord_link', 'server_ip', 'updated']
    fieldsets = (
        ('اطلاعات سرور', {
            'fields': ('discord_invite_link', 'minecraft_server_ip'),
            'description': '💬 لینک دعوت دیسکورد و آی‌پی سرور ماینکرفت'
        }),
        ('اطلاعات ادمین‌ها', {
            'fields': ('admin_info_text',),
            'description': '👤 اطلاعات ادمین‌های سرور - می‌توانید HTML استفاده کنید'
        }),
        ('اطلاعات اضافی', {
            'fields': ('additional_info',),
            'description': 'ℹ️ هرگونه اطلاعات اضافی برای نمایش در صفحه More Info - HTML مجاز است'
        }),
    )
    readonly_fields = ['updated']

    def discord_link(self, obj):
        if obj.discord_invite_link:
            return format_html('<a href="{}" target="_blank">لینک دیسکورد</a>', obj.discord_invite_link)
        return 'تنظیم نشده'
    discord_link.short_description = 'دیسکورد'

    def server_ip(self, obj):
        return obj.minecraft_server_ip or 'تنظیم نشده'
    server_ip.short_description = 'آی‌پی سرور'

    def get_queryset(self, request):
        SiteInfo.load()
        return super().get_queryset(request).filter(pk=1)