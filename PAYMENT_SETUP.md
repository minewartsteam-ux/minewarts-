# راهنمای تنظیم درگاه پرداخت زرین‌پال

## تنظیمات اولیه

### 1. دریافت Merchant ID از زرین‌پال

1. به سایت [زرین‌پال](https://www.zarinpal.com) بروید
2. ثبت‌نام یا ورود به حساب کاربری
3. از پنل کاربری، Merchant ID خود را دریافت کنید

### 2. تنظیم در محیط توسعه (Sandbox)

برای تست در محیط توسعه، از Merchant ID تست استفاده کنید:
- Merchant ID تست: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

### 3. تنظیم متغیرهای محیطی

در فایل `settings.py` یا از طریق متغیرهای محیطی:

```python
# در settings.py یا .env
ZARINPAL_MERCHANT_ID = 'your-merchant-id-here'
ZARINPAL_SANDBOX = 'True'  # برای تست از True استفاده کنید
```

یا از طریق متغیرهای محیطی سیستم:

```bash
# Windows PowerShell
$env:ZARINPAL_MERCHANT_ID="your-merchant-id"
$env:ZARINPAL_SANDBOX="True"

# Linux/Mac
export ZARINPAL_MERCHANT_ID="your-merchant-id"
export ZARINPAL_SANDBOX="True"
```

### 4. نصب پکیج‌های مورد نیاز

```bash
pip install requests
```

یا:

```bash
pip install -r requirements.txt
```

## استفاده در محیط تولید

برای استفاده در محیط تولید:

1. `ZARINPAL_SANDBOX` را به `False` تغییر دهید
2. Merchant ID واقعی خود را وارد کنید
3. مطمئن شوید که callback URL در پنل زرین‌پال تنظیم شده است

## تست پرداخت

1. یک سفارش ایجاد کنید
2. روش پرداخت "پرداخت آنلاین" را انتخاب کنید
3. به درگاه پرداخت هدایت می‌شوید
4. در محیط Sandbox می‌توانید از کارت‌های تست استفاده کنید

## کارت‌های تست زرین‌پال

- شماره کارت: `6037-9971-0000-0000`
- CVV2: `123`
- تاریخ انقضا: هر تاریخ آینده
- رمز دوم: `123456`

## نکات مهم

- در محیط Sandbox، پرداخت‌ها واقعی نیستند
- برای استفاده واقعی، حتماً Merchant ID واقعی را وارد کنید
- Callback URL باید به صورت کامل و صحیح تنظیم شود
- در محیط تولید، HTTPS الزامی است

