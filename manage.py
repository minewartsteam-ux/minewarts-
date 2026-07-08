#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    # تنظیم می‌کند که جنگو از کدام فایل تنظیمات استفاده کند
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myshop.settings')
    try:
        # تابع اصلی برای اجرای دستورات مدیریتی جنگو را وارد می‌کند
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # اگر جنگو نصب نباشد یا محیط مجازی فعال نباشد، این خطا نمایش داده می‌شود
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    # دستوراتی که در ترمینال وارد می‌کنید (مثل runserver, migrate) به این تابع ارسال می‌شوند
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()