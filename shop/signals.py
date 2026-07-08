"""
Signals برای پردازش خودکار عکس‌ها
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import os
from .models import SiteSettings


@receiver(pre_save, sender=SiteSettings)
def resize_background_image(sender, instance, **kwargs):
    """
    Resize کردن خودکار عکس پس‌زمینه قبل از ذخیره
    """
    # بررسی اینکه آیا عکس جدید آپلود شده یا نه
    if instance.background_image:
        try:
            # بررسی اینکه آیا عکس تغییر کرده
            if instance.pk:
                try:
                    old_instance = SiteSettings.objects.get(pk=instance.pk)
                    # اگر عکس تغییر نکرده، resize نکن
                    if old_instance.background_image == instance.background_image:
                        return
                except SiteSettings.DoesNotExist:
                    pass
            
            # خواندن فایل آپلود شده
            if hasattr(instance.background_image, 'read'):
                # فایل از memory است
                instance.background_image.seek(0)
                img = Image.open(instance.background_image)
                instance.background_image.seek(0)
            elif hasattr(instance.background_image, 'temporary_file_path'):
                # فایل موقت در سیستم فایل است
                img = Image.open(instance.background_image.temporary_file_path())
            else:
                # فایل از path است
                img = Image.open(instance.background_image.path)
            
            # تبدیل به RGB اگر RGBA است (برای JPG)
            if img.mode in ('RGBA', 'LA', 'P'):
                # ایجاد پس‌زمینه سفید
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # اندازه مناسب برای پس‌زمینه: 1920x1080 (Full HD)
            # اما نسبت تصویر را حفظ می‌کنیم
            max_width = 1920
            max_height = 1080
            
            # محاسبه اندازه جدید با حفظ نسبت
            original_width, original_height = img.size
            
            # اگر عکس از اندازه حداکثر کوچکتر است، resize نکن
            if original_width > max_width or original_height > max_height:
                # محاسبه نسبت
                width_ratio = max_width / original_width
                height_ratio = max_height / original_height
                ratio = min(width_ratio, height_ratio)
                
                # محاسبه اندازه جدید
                new_width = int(original_width * ratio)
                new_height = int(original_height * ratio)
                
                # Resize کردن عکس با کیفیت بالا
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # ذخیره عکس resize شده
                img_io = BytesIO()
                img.save(img_io, format='JPEG', quality=85, optimize=True)
                img_io.seek(0)
                
                # جایگزین کردن فایل اصلی
                filename = os.path.basename(instance.background_image.name) if hasattr(instance.background_image, 'name') else 'background.jpg'
                
                # ذخیره فایل جدید
                instance.background_image.save(
                    filename,
                    ContentFile(img_io.read()),
                    save=False
                )
                
        except Exception as e:
            # اگر خطایی رخ داد، عکس را بدون resize ذخیره کن
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"خطا در resize کردن عکس پس‌زمینه: {str(e)}")
            pass

