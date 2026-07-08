import subprocess
import os
import shutil

# مسیر به فایل manage.py پروژه شما (فرض بر این است که این اسکریپت در ریشه پروژه قرار دارد)
manage_py_path = 'manage.py'

# تنظیمات Django (اگر لازم باشد، مسیر settings.py را مشخص کنید)
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings') # 'your_project' را با نام پروژه خود جایگزین کنید

# مسیر STATIC_ROOT که در settings.py تعریف شده است
# فرض می‌کنیم STATIC_ROOT در settings.py شما به درستی تنظیم شده است.
# اگر می‌خواهید مطمئن شوید که پوشه STATIC_ROOT قبل از collectstatic خالی است،
# باید آن را بخوانید و حذف کنید.
# در اینجا، ما فقط دستور collectstatic را اجرا می‌کنیم.
# اگر نیاز به پاک کردن STATIC_ROOT دارید، می‌توانید این بخش را اضافه کنید:

# از تنظیمات Django برای خواندن STATIC_ROOT استفاده می‌کنیم
try:
    from django.conf import settings
    static_root = settings.STATIC_ROOT
    if not static_root:
        print("خطا: STATIC_ROOT در settings.py تعریف نشده است.")
        exit()

    # حذف پوشه STATIC_ROOT قبل از اجرای collectstatic (اختیاری)
    if os.path.exists(static_root):
        print(f"در حال حذف پوشه موجود STATIC_ROOT: {static_root}")
        try:
            shutil.rmtree(static_root)
            print("پوشه STATIC_ROOT با موفقیت حذف شد.")
        except OSError as e:
            print(f"خطا در حذف پوشه STATIC_ROOT: {e.strerror}")
            # اگر حذف موفقیت آمیز نبود، ممکن است collectstatic خطا بدهد
            # exit() # می‌توانید اجرای برنامه را متوقف کنید یا ادامه دهید

    # ایجاد مجدد پوشه STATIC_ROOT (collectstatic خود این کار را انجام می‌دهد، اما برای اطمینان)
    os.makedirs(static_root, exist_ok=True)
    print(f"پوشه STATIC_ROOT ایجاد شد یا از قبل وجود داشت: {static_root}")

except ImportError:
    print("خطا: قادر به وارد کردن تنظیمات Django نیست. مطمئن شوید که در محیط مجازی صحیح هستید و manage.py در دسترس است.")
    # در این حالت، ما فقط دستور را اجرا می‌کنیم بدون اینکه STATIC_ROOT را بدانیم یا پاک کنیم
    static_root = None # علامت‌گذاری که STATIC_ROOT را نمی‌دانیم

except AttributeError:
    print("خطا: STATIC_ROOT در تنظیمات Django یافت نشد. لطفاً آن را در settings.py تعریف کنید.")
    static_root = None # علامت‌گذاری که STATIC_ROOT را نمی‌دانیم


# اجرای دستور collectstatic
print("در حال اجرای دستور 'python manage.py collectstatic'...")
try:
    # استفاده از subprocess.run برای اجرای دستور
    # اگر در محیط مجازی هستید، نیازی به تنظیم DJANGO_SETTINGS_MODULE نیست
    # اگر نیست، ممکن است لازم باشد آن را تنظیم کنید
    result = subprocess.run(
        ['python', manage_py_path, 'collectstatic', '--noinput'], # --noinput برای جلوگیری از پرسیدن تاییدیه
        capture_output=True,
        text=True,
        check=True, # اگر دستور با کد خطا اجرا شود، exception پرتاب می‌کند
        cwd=os.path.dirname(os.path.abspath(__file__)) # اطمینان از اجرای دستور در دایرکتوری صحیح
    )
    print("خروجی دستور collectstatic:")
    print(result.stdout)
    if result.stderr:
        print("خطاهای دستور collectstatic (stderr):")
        print(result.stderr)
    print("دستور 'python manage.py collectstatic' با موفقیت اجرا شد.")

except FileNotFoundError:
    print(f"خطا: فایل '{manage_py_path}' یافت نشد. مطمئن شوید که اسکریپت در ریشه پروژه قرار دارد.")
except subprocess.CalledProcessError as e:
    print(f"خطا در اجرای دستور 'python manage.py collectstatic':")
    print(f"کد خروجی: {e.returncode}")
    print(f"خروجی استاندارد (stdout): {e.stdout}")
    print(f"خطای استاندارد (stderr): {e.stderr}")
except Exception as e:
    print(f"یک خطای غیرمنتظره رخ داد: {e}")
