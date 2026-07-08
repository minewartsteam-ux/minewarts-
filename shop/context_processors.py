"""
Context processor برای دسترسی به تنظیمات سایت در تمام template ها
"""
from .models import SiteSettings
from django.db import OperationalError

def site_settings(request):
    """
    اضافه کردن تنظیمات سایت به context تمام template ها
    """
    try:
        settings = SiteSettings.load()
    except OperationalError:
        # اگر فیلدها وجود ندارند، یک تنظیمات پیش‌فرض برگردان
        class DefaultSettings:
            primary_color = '#4CAF50'
            secondary_color = '#FFC107'
            accent_color = '#03A9F4'
            dark_bg_color = '#121212'
            card_bg_color = 'rgba(30, 30, 30, 0.85)'
            text_light_color = '#E0E0E0'
            text_muted_color = '#9E9E9E'
            navbar_title = None
            footer_text = '© 2024 فروشگاه ماینکرفت - ساخته شده با ❤️ و Django'
            site_name = 'فروشگاه ماینکرفت'
            background_image = None
        settings = DefaultSettings()
    
    return {
        'site_settings': settings,
        'site_background_image': settings.background_image.url if settings.background_image else None,
    }

