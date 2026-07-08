import os
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "به‌روزرسانی ایمیل ارسال‌کننده و رمز اپلیکیشن و ذخیره در فایل .env"

    def handle(self, *args, **options):
        base_dir = Path(__file__).resolve().parents[3]  # project root
        env_path = base_dir / ".env"

        self.stdout.write(self.style.MIGRATE_HEADING("✉️  پیکربندی ایمیل ارسال‌کننده"))
        self.stdout.write(
            "این دستور ایمیل و app password را در فایل .env ذخیره می‌کند تا برای ارسال ایمیل‌های تایید استفاده شود."
        )

        email = input("ایمیل ارسال‌کننده (مثلاً gmail): ").strip()
        if not email:
            raise CommandError("ایمیل نباید خالی باشد.")

        app_password = input("App Password (رمز ۱۶ رقمی Gmail یا SMTP): ").strip()
        if not app_password:
            raise CommandError("رمز نباید خالی باشد.")

        host = input("SMTP HOST [smtp.gmail.com]: ").strip() or "smtp.gmail.com"
        port_input = input("SMTP PORT [465]: ").strip()
        port = port_input or "465"

        # خواندن مقادیر قبلی برای حفظ سایر کلیدها
        env_data = {}
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                env_data[k.strip()] = v.strip()

        env_data.update(
            {
                "SKY_SMTP_SERVER": host,
                "SKY_SMTP_PORT": str(port),
                "SKY_SMTP_USER": email,
                "SKY_SMTP_PASS": app_password,
                "DEFAULT_FROM_EMAIL": email,
            }
        )

        lines = [f"{k}={v}" for k, v in env_data.items()]
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        self.stdout.write(self.style.SUCCESS("✅ تنظیمات ایمیل با موفقیت ذخیره شد در .env"))
        self.stdout.write(self.style.HTTP_INFO("برای اعمال تنظیمات، سرور Django را ریستارت کنید."))

