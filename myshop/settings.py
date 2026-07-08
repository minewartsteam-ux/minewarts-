# ================================================================
# settings.py - فایل کامل تنظیمات پروژه Mine Warts
# برای دپلوی روی Railway با PostgreSQL
# ================================================================

import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# ================================================================
# بارگذاری .env
# ================================================================
def load_env():
    """بارگذاری فایل .env با پشتیبانی از نقل قول و کامنت"""
    env_path = BASE_DIR / '.env'
    if not env_path.exists():
        return
    
    for line in env_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        if '=' not in line:
            continue
            
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip()
        
        # حذف نقل قول‌ها
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1]
        
        os.environ.setdefault(key, value)

load_env()

# ================================================================
# تنظیمات پایه
# ================================================================
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-your-secret-key-here')
SITE_NAME = os.environ.get('SITE_NAME', 'Mine Warts')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'no-reply@minewarts.com')

DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() == 'true'

# ================================================================
# ALLOWED_HOSTS
# ================================================================
if DEBUG:
    ALLOWED_HOSTS = ['*']
else:
    allowed_hosts = os.environ.get('DJANGO_ALLOWED_HOSTS', '')
    if allowed_hosts:
        ALLOWED_HOSTS = [h.strip() for h in allowed_hosts.split(',') if h.strip()]
    else:
        ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# ================================================================
# APPS
# ================================================================
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'whitenoise.runserver_nostatic',  # برای سرویس استاتیک فایل‌ها
    'shop.apps.ShopConfig',
    'cart',
    'orders',
    'accounts',
    'myshop.server',
]

# فقط در حالت DEBUG به INSTALLED_APPS اضافه شود
if DEBUG:
    try:
        import debug_toolbar
        INSTALLED_APPS.append('debug_toolbar')
    except ImportError:
        pass

# ================================================================
# MIDDLEWARE
# ================================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # برای سرویس استاتیک فایل‌ها
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'cart.middleware.CartMiddleware',
    'myshop.security_middleware.SecurityHeadersMiddleware',
    'myshop.security_middleware.RateLimitMiddleware',
    'myshop.security_middleware.SecurityLoggingMiddleware',
    'myshop.security_middleware.PerformanceMiddleware',
]

# فقط در حالت DEBUG به MIDDLEWARE اضافه شود
if DEBUG:
    try:
        import debug_toolbar
        # اضافه کردن بعد از SecurityMiddleware و قبل از SessionMiddleware
        security_index = MIDDLEWARE.index('django.middleware.security.SecurityMiddleware')
        MIDDLEWARE.insert(security_index + 1, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    except ImportError:
        pass

# ================================================================
# TEMPLATES
# ================================================================
ROOT_URLCONF = 'myshop.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'cart.context_processors.cart',
                'shop.context_processors.site_settings',
                'accounts.context_processors.user_ticket_access',
            ],
        },
    },
]

WSGI_APPLICATION = 'myshop.wsgi.application'

# ================================================================
# DATABASE - پشتیبانی از PostgreSQL در Railway و SQLite در لوکال
# ================================================================
if os.environ.get('DATABASE_URL'):
   
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
   
    DATABASES['default']['OPTIONS'] = {
        'connect_timeout': 10,
        'options': '-c statement_timeout=30000ms',
    }
else:
  
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ================================================================
# AUTH PASSWORD VALIDATORS
# ================================================================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {
            'user_attributes': ('username', 'email', 'first_name', 'last_name'),
            'max_similarity': 0.7,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ================================================================
# LOGIN / LOGOUT
# ================================================================
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# ================================================================
# SESSION
# ================================================================
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7 * 2  # 2 هفته
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_NAME = 'sessionid_secure'
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# ================================================================
# CSRF
# ================================================================
CSRF_COOKIE_AGE = 60 * 60 * 24 * 7  # 1 هفته
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_NAME = 'csrftoken_secure'
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'
CSRF_USE_SESSIONS = True
CSRF_FAILURE_VIEW = 'django.views.csrf.csrf_failure'
CSRF_TRUSTED_ORIGINS = []

# ================================================================
# SECURITY
# ================================================================
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
SECURE_CROSS_ORIGIN_EMBEDDER_POLICY = 'require-corp'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# ================================================================
# PRODUCTION SECURITY - فعال برای Railway
# ================================================================
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000  # 1 سال
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # اعتبارسنجی ALLOWED_HOSTS
    if ALLOWED_HOSTS == ['*'] or not ALLOWED_HOSTS:
        raise ValueError("❌ ALLOWED_HOSTS cannot be empty or '*' in production!")

# ================================================================
# INTERNATIONALIZATION
# ================================================================
LANGUAGE_CODE = 'fa-ir'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True

# ================================================================
# EMAIL
# ================================================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 465
EMAIL_HOST_USER = 'minewarts.team@gmail.com'
EMAIL_HOST_PASSWORD = 'suplbjkvfpbbzqjt'
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# ================================================================
# STATIC / MEDIA - تنظیمات برای Railway
# ================================================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# استفاده از WhiteNoise برای سرویس فایل‌های استاتیک در Production
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CART_SESSION_ID = 'cart'

# ================================================================
# ZARINPAL
# ================================================================

# ✅ مرچنت آیدی صحیح برای سندباکس
ZARINPAL_MERCHANT_ID = "00000000-0000-0000-0000-000000000000"  # ← این مقدار صحیح است
# یا از محیط بخوانید:
# ZARINPAL_MERCHANT_ID = os.environ.get('ZARINPAL_MERCHANT_ID', '00000000-0000-0000-0000-000000000000')

ZARINPAL_SANDBOX = True  # ← برای تست در محیط سندباکس

if ZARINPAL_SANDBOX:
    ZARINPAL_REQUEST_URL = 'https://sandbox.zarinpal.com/pg/v4/payment/request.json'
    ZARINPAL_VERIFY_URL = 'https://sandbox.zarinpal.com/pg/v4/payment/verify.json'
    ZARINPAL_STARTPAY_URL = 'https://sandbox.zarinpal.com/pg/StartPay/'
else:
    ZARINPAL_REQUEST_URL = 'https://api.zarinpal.com/pg/v4/payment/request.json'
    ZARINPAL_VERIFY_URL = 'https://api.zarinpal.com/pg/v4/payment/verify.json'
    ZARINPAL_STARTPAY_URL = 'https://www.zarinpal.com/pg/StartPay/'

# ================================================================
# MINECRAFT RCON (Rank provisioning)
# ================================================================
MINECRAFT_RCON_HOST = os.environ.get('MINECRAFT_RCON_HOST', '127.0.0.1')
MINECRAFT_RCON_PORT = int(os.environ.get('MINECRAFT_RCON_PORT', '25575'))
MINECRAFT_RCON_PASSWORD = os.environ.get('MINECRAFT_RCON_PASSWORD', '')
MINECRAFT_RCON_TIMEOUT = int(os.environ.get('MINECRAFT_RCON_TIMEOUT', '10'))
RANK_MAPPING_PATH = BASE_DIR / 'config' / 'rank_mapping.json'
RANK_MAX_RETRIES = int(os.environ.get('RANK_MAX_RETRIES', '20'))

# ================================================================
# SECURITY HEADERS - CSP
# ================================================================
CSP_EXTRA_DOMAINS = [
    'https://cdn.jsdelivr.net',
    'https://fonts.googleapis.com',
    'https://fonts.gstatic.com',
]

CSP_API_DOMAINS = [
    'https://api.zarinpal.com',
    'https://sandbox.zarinpal.com',
]

CSP_WEBSOCKET_DOMAINS = []

CSP_UNSAFE_INLINE = DEBUG

# ================================================================
# RATE LIMIT
# ================================================================
RATE_LIMIT_PER_MINUTE = 60
RATE_LIMIT_EXEMPT_PATHS = [
    '/admin/',
    '/api/webhook/',
]
RATE_LIMIT_USE_CACHE = True

# ================================================================
# PERFORMANCE
# ================================================================
SLOW_REQUEST_THRESHOLD = 1.0
PERFORMANCE_EXEMPT_PATHS = [
    '/static/',
    '/media/',
]

# ================================================================
# CACHE
# ================================================================
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# ================================================================
# JAZZMIN
# ================================================================
JAZZMIN_SETTINGS = {
    "site_title": "Mine Warts",
    "site_header": "",
    "site_brand": "",
    "site_logo": None,
    "welcome_sign": "",
    "language_chooser": False,
    "hide_models": [],
    "order_with_respect_to": ["auth", "core"],
    "menu_icon_size": "1.5rem",
    "navigation": [
        {
            "name": "داشبورد",
            "url": "/admin/dashboard/",
            "icon": "fas fa-tachometer-alt",
            "permissions": ["auth.view_user"],
        },
        {"app": "shop", "icon": "fas fa-shopping-cart", "models": [
            {"model": "product", "icon": "fas fa-cube"},
            {"model": "category", "icon": "fas fa-tags"},
        ]},
        {"app": "orders", "icon": "fas fa-clipboard-list", "models": [
            {"model": "order", "icon": "fas fa-file-invoice"},
        ]},
        {"app": "accounts", "icon": "fas fa-headset", "models": [
            {"model": "supportticket", "icon": "fas fa-ticket-alt"},
            {"model": "supportmessage", "icon": "fas fa-comments"},
        ]},
    ],
    "ui": {
        "theme": "dark.css",
        "sidebar_navigation": "vertical",
        "navbar_fixed": False,
        "sidebar_fixed": False,
        "show_sidebar": False,
        "navigation_expanded": True,
        "actions_sticky_top": True,
    },
    "custom_css": "admin_custom.css",
    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "auth.user": "collapsible",
        "auth.group": "vertical_tabs",
    },
}

# ================================================================
# LOGGING
# ================================================================
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} - {levelname} - {module} - {message}',
            'style': '{',
        },
        'simple': {
            'format': '{asctime} - {levelname} - {message}',
            'style': '{',
        },
        'security': {
            'format': '{asctime} - {levelname} - {name} - {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': LOGS_DIR / 'django.log',
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        'security_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': LOGS_DIR / 'security.log',
            'formatter': 'security',
            'encoding': 'utf-8',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': LOGS_DIR / 'errors.log',
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        'performance_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': LOGS_DIR / 'performance.log',
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO' if not DEBUG else 'DEBUG',
            'propagate': True,
        },
        'django.security': {
            'handlers': ['security_file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'security': {
            'handlers': ['security_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'security.ratelimit': {
            'handlers': ['security_file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'security.headers': {
            'handlers': ['security_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'performance': {
            'handlers': ['performance_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['file'],
            'level': 'WARNING' if not DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# ================================================================
# SECURITY EXEMPT PATHS
# ================================================================
SECURITY_HEADERS_EXEMPT = [
    '/admin/',
    '/api/webhook/',
    '/media/',
]

# ================================================================
# END OF SETTINGS
# ================================================================