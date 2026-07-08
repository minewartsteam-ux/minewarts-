from django.apps import AppConfig

class ServerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myshop.server'  # ✅ مهم: مسیر کامل را مشخص کنید
    verbose_name = 'وضعیت سرور'