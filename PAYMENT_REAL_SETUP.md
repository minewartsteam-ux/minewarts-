# راهنمای کامل تنظیم پرداخت واقعی کارت به کارت

## 🔐 تنظیمات امنیتی و اتصال به درگاه واقعی

### مرحله 1: دریافت Merchant ID واقعی از زرین‌پال

1. به سایت [زرین‌پال](https://www.zarinpal.com) بروید
2. ثبت‌نام یا ورود به حساب کاربری
3. از بخش "درگاه پرداخت" → "دریافت Merchant ID" اقدام کنید
4. Merchant ID واقعی خود را کپی کنید (فرمت: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)

### مرحله 2: تنظیم متغیرهای محیطی

#### روش 1: استفاده از فایل .env (پیشنهادی)

یک فایل `.env` در ریشه پروژه ایجاد کنید:

```env
ZARINPAL_MERCHANT_ID=your-real-merchant-id-here
ZARINPAL_SANDBOX=False
```

#### روش 2: تنظیم در Windows PowerShell

```powershell
$env:ZARINPAL_MERCHANT_ID="your-real-merchant-id"
$env:ZARINPAL_SANDBOX="False"
```

#### روش 3: تنظیم در Linux/Mac

```bash
export ZARINPAL_MERCHANT_ID="your-real-merchant-id"
export ZARINPAL_SANDBOX="False"
```

### مرحله 3: تنظیم Callback URL در پنل زرین‌پال

1. وارد پنل زرین‌پال شوید
2. به بخش "تنظیمات درگاه" بروید
3. Callback URL را تنظیم کنید:
   ```
   https://yourdomain.com/orders/payment/callback/
   ```
   یا برای تست محلی:
   ```
   http://127.0.0.1:8000/orders/payment/callback/
   ```

### مرحله 4: فعال‌سازی HTTPS (برای Production)

برای استفاده واقعی، حتماً باید از HTTPS استفاده کنید:

1. گواهینامه SSL دریافت کنید
2. در `settings.py` تنظیمات زیر را فعال کنید:
   ```python
   SESSION_COOKIE_SECURE = True
   CSRF_COOKIE_SECURE = True
   SECURE_SSL_REDIRECT = True
   ```

## 🔒 ویژگی‌های امنیتی پیاده‌سازی شده

✅ **SSL Verification**: تمام ارتباطات با درگاه از طریق HTTPS و با بررسی گواهینامه SSL
✅ **Input Validation**: اعتبارسنجی کامل تمام ورودی‌ها
✅ **Timeout Protection**: جلوگیری از hang شدن با timeout 15 ثانیه
✅ **Session Security**: ذخیره امن authority در session
✅ **Error Handling**: مدیریت کامل خطاها
✅ **CSRF Protection**: محافظت کامل در برابر CSRF attacks

## 💳 نحوه کار پرداخت واقعی

1. کاربر سفارش را ثبت می‌کند
2. به صفحه پرداخت هدایت می‌شود
3. روی "پرداخت با زرین‌پال" کلیک می‌کند
4. به درگاه واقعی زرین‌پال هدایت می‌شود
5. اطلاعات کارت را وارد می‌کند
6. پرداخت انجام می‌شود
7. به سایت بازمی‌گردد و پرداخت تایید می‌شود

## ⚠️ نکات مهم

- **Merchant ID واقعی**: حتماً از Merchant ID واقعی استفاده کنید (نه تست)
- **HTTPS**: در production حتماً از HTTPS استفاده کنید
- **Callback URL**: باید دقیقاً در پنل زرین‌پال تنظیم شود
- **امنیت**: تمام اطلاعات با SSL رمزنگاری می‌شوند
- **لاگ‌ها**: تمام تراکنش‌ها در پنل زرین‌پال ثبت می‌شوند

## 🧪 تست قبل از استفاده واقعی

1. ابتدا با Sandbox تست کنید
2. از کارت‌های تست استفاده کنید
3. مطمئن شوید که callback درست کار می‌کند
4. سپس به حالت واقعی تغییر دهید

## 📞 پشتیبانی

در صورت مشکل:
- مستندات زرین‌پال: https://www.zarinpal.com/docs
- پشتیبانی زرین‌پال: support@zarinpal.com


