# راهنمای رفع مشکل جداول تیکت

## مشکل
خطای `no such table: accounts_supportticket` به این معنی است که جداول تیکت در دیتابیس ایجاد نشده‌اند.

## راه حل

### روش 1: اجرای Migration (توصیه می‌شود)

در terminal/PowerShell، دستورات زیر را به ترتیب اجرا کنید:

```bash
cd "f:\mc site\minecraft_shop1 - Copy"
python manage.py migrate accounts
python manage.py migrate
```

### روش 2: اگر روش 1 کار نکرد

اگر migration اجرا نشد، از دستور زیر استفاده کنید:

```bash
python manage.py migrate accounts 0001 --fake
python manage.py migrate
```

### روش 3: اجرای مستقیم SQL

اگر هیچکدام کار نکرد، فایل `create_tables_manual.py` را اجرا کنید:

```bash
python create_tables_manual.py
```

## بررسی

بعد از اجرای دستورات، بررسی کنید:

```bash
python manage.py showmigrations accounts
```

باید ببینید:
```
accounts
 [X] 0001_initial
```

## تست

برای تست، این دستور را اجرا کنید:

```bash
python -c "from accounts.models import SupportTicket; print('OK:', SupportTicket.objects.count())"
```

اگر خطایی نداد، مشکل حل شده است!
