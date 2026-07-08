"""
Security Middleware - هدرهای امنیتی پیشرفته برای Django
نسخه کاملاً بهینه و حرفه‌ای با پشتیبانی WhiteNoise
"""
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse, HttpResponse, StreamingHttpResponse
from django.core.cache import cache
import re
import logging
from urllib.parse import urlparse


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    اضافه کردن هدرهای امنیتی پیشرفته به تمام پاسخ‌ها
    """

    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        self._is_debug = settings.DEBUG
        self._is_secure = not self._is_debug and getattr(settings, 'SECURE_SSL_REDIRECT', False)
        self._exempt_paths = getattr(settings, 'SECURITY_HEADERS_EXEMPT', [])
        self._logger = logging.getLogger('security.headers')
        
        # ✅ اضافه کردن تنظیمات CSP از settings
        self._csp_extra_domains = getattr(settings, 'CSP_EXTRA_DOMAINS', [])
        self._csp_api_domains = getattr(settings, 'CSP_API_DOMAINS', [])
        self._csp_ws_domains = getattr(settings, 'CSP_WEBSOCKET_DOMAINS', [])
        self._csp_unsafe_inline = getattr(settings, 'CSP_UNSAFE_INLINE', False)

    def __call__(self, request):
        response = self.get_response(request)
        
        # بررسی مسیرهای معاف
        if not self._is_path_exempt(request.path):
            self._add_security_headers(response, request)
        
        return response

    def _is_path_exempt(self, path):
        """بررسی اینکه آیا مسیر از هدرهای امنیتی معاف است"""
        for exempt_path in self._exempt_paths:
            if path.startswith(exempt_path):
                return True
        return False

    def _add_security_headers(self, response, request):
        """
        افزودن هدرهای امنیتی به پاسخ
        """
        try:
            # ===== هدرهای پایه (همیشه فعال) =====
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['X-XSS-Protection'] = '1; mode=block'
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # ===== Permissions Policy (مدرن) =====
            response['Permissions-Policy'] = (
                'accelerometer=(), '
                'autoplay=(), '
                'camera=(), '
                'encrypted-media=(), '
                'fullscreen=(self), '
                'geolocation=(), '
                'gyroscope=(), '
                'magnetometer=(), '
                'microphone=(), '
                'midi=(), '
                'payment=(), '
                'picture-in-picture=(), '
                'sync-xhr=(), '
                'usb=()'
            )

            # ===== HSTS (فقط Production) =====
            if self._is_secure and not self._is_debug:
                response['Strict-Transport-Security'] = (
                    'max-age=31536000; '
                    'includeSubDomains; '
                    'preload'
                )

            # ===== Content Security Policy =====
            if not self._is_debug:
                csp = self._build_csp_policy(request)
                response['Content-Security-Policy'] = csp

            # ===== حذف هدرهای اطلاعاتی =====
            response['Server'] = 'Secure-Server'
            if 'X-Powered-By' in response:
                del response['X-Powered-By']

            # ===== Cache Control (برای صفحات امنیتی) =====
            if self._is_secure and not self._is_static_file(request.path):
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'

        except Exception as e:
            self._logger.error(f"Error adding security headers: {e}")

    def _is_static_file(self, path):
        """بررسی فایل‌های استاتیک برای کش کردن"""
        static_extensions = ('.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp', '.woff', '.woff2', '.ttf')
        return any(path.endswith(ext) for ext in static_extensions)

    def _build_csp_policy(self, request):
        """
        ساخت Content Security Policy پویا
        """
        default_src = "'self'"
        
        # ✅ بهبود CSP - عدم استفاده از unsafe-inline در Production
        if self._csp_unsafe_inline or self._is_debug:
            script_src = "'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com"
            style_src = "'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com"
        else:
            script_src = "'self' https://cdn.jsdelivr.net https://fonts.googleapis.com"
            style_src = "'self' https://cdn.jsdelivr.net https://fonts.googleapis.com"
        
        font_src = "'self' https://fonts.gstatic.com"
        img_src = "'self' data: https: http:"
        connect_src = "'self'"
        frame_src = "'none'"
        object_src = "'none'"
        base_uri = "'self'"
        form_action = "'self'"

        # ===== اضافه کردن دامنه‌های اضافی =====
        if self._csp_extra_domains:
            domains_str = ' '.join(self._csp_extra_domains)
            script_src += f' {domains_str}'
            style_src += f' {domains_str}'
            img_src += f' {domains_str}'

        # ===== اضافه کردن API URLs =====
        if self._csp_api_domains:
            connect_src += ' ' + ' '.join(self._csp_api_domains)

        # ===== اضافه کردن WebSocket =====
        if self._csp_ws_domains:
            connect_src += ' ' + ' '.join(self._csp_ws_domains)

        csp_parts = [
            f"default-src {default_src}",
            f"script-src {script_src}",
            f"style-src {style_src}",
            f"font-src {font_src}",
            f"img-src {img_src}",
            f"connect-src {connect_src}",
            f"frame-src {frame_src}",
            f"object-src {object_src}",
            f"base-uri {base_uri}",
            f"form-action {form_action}",
            "upgrade-insecure-requests",
            "block-all-mixed-content",
        ]

        return '; '.join(csp_parts)


# ============================================================
# Rate Limit Middleware (فیکس شده)
# ============================================================

class RateLimitMiddleware(MiddlewareMixin):
    """
    محدودیت نرخ درخواست با استفاده از Cache
    """
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        self._exempt_paths = getattr(settings, 'RATE_LIMIT_EXEMPT_PATHS', [])
        self._max_requests = getattr(settings, 'RATE_LIMIT_PER_MINUTE', 60)
        self._use_cache = getattr(settings, 'RATE_LIMIT_USE_CACHE', True)
        self._logger = logging.getLogger('security.ratelimit')

    def __call__(self, request):
        # بررسی مسیرهای معاف
        if self._is_path_exempt(request.path):
            return self.get_response(request)

        # محدودیت برای درخواست‌های POST و API
        if request.method in ['POST', 'PUT', 'DELETE']:
            if not self._check_rate_limit(request):
                self._logger.warning(
                    f"Rate limit exceeded: {request.method} {request.path} "
                    f"from {self._get_client_ip(request)}"
                )
                return JsonResponse({
                    'error': 'Too Many Requests',
                    'message': 'لطفاً کمی صبر کنید و دوباره تلاش کنید.',
                    'retry_after': 60
                }, status=429)
        
        response = self.get_response(request)
        
        # اضافه کردن هدر Rate Limit
        if hasattr(request, '_rate_limit_info'):
            response['X-RateLimit-Limit'] = str(self._max_requests)
            response['X-RateLimit-Remaining'] = str(request._rate_limit_info.get('remaining', 0))
        
        return response

    def _is_path_exempt(self, path):
        """بررسی مسیرهای معاف از محدودیت"""
        for exempt_path in self._exempt_paths:
            if path.startswith(exempt_path):
                return True
        return False

    def _get_client_ip(self, request):
        """دریافت IP کاربر با پشتیبانی از پروکسی - فیکس شده"""
        # ✅ پشتیبانی از Cloudflare و سایر پروکسی‌ها
        cf_connecting_ip = request.META.get('HTTP_CF_CONNECTING_IP')
        if cf_connecting_ip:
            return cf_connecting_ip
        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # گرفتن اولین IP (IP واقعی کاربر)
            ips = [ip.strip() for ip in x_forwarded_for.split(',')]
            # فیلتر کردن IPهای داخلی
            for ip in ips:
                if not ip.startswith(('10.', '172.16.', '192.168.', '127.')):
                    return ip
            return ips[0]
        
        return request.META.get('REMOTE_ADDR', 'unknown')

    def _check_rate_limit(self, request):
        """بررسی محدودیت نرخ درخواست - فیکس شده"""
        if not self._use_cache:
            return True
        
        client_ip = self._get_client_ip(request)
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        key = f'rate_limit_{user_id}_{client_ip}_{request.path}'
        
        try:
            count = cache.get(key, 0)
            
            if count >= self._max_requests:
                request._rate_limit_info = {'remaining': 0}
                return False
            
            # افزایش شمارنده
            cache.set(key, count + 1, 60)
            request._rate_limit_info = {
                'remaining': self._max_requests - count - 1
            }
            return True
            
        except Exception as e:
            self._logger.error(f"Rate limit error: {e}")
            # ✅ در صورت خطا، اجازه ادامه بده (fail open)
            return True


# ============================================================
# Security Logging Middleware (فیکس شده)
# ============================================================

class SecurityLoggingMiddleware(MiddlewareMixin):
    """
    لاگ‌گیری رویدادهای امنیتی
    """
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        self._logger = logging.getLogger('security')
        self._suspicious_patterns = [
            (r'\.\./', 'Path Traversal'),
            (r'<script>', 'XSS Attempt'),
            (r'union\s+select', 'SQL Injection'),
            (r'exec\s*\(', 'Command Injection'),
            (r'/\*.*?\*/', 'SQL Comment Injection'),
            (r'--', 'SQL Comment Injection'),
            (r'%00', 'Null Byte Injection'),
            (r'etc/passwd', 'File Access Attempt'),
            (r'\.env', 'Environment File Access'),
            (r'\.git', 'Git Directory Access'),
        ]

    def __call__(self, request):
        # لاگ درخواست‌های مشکوک
        self._log_suspicious_requests(request)
        
        response = self.get_response(request)
        
        # لاگ رویدادهای امنیتی
        if response.status_code in [403, 429, 401, 400, 404]:
            self._log_security_event(request, response)
        
        return response

    def _log_suspicious_requests(self, request):
        """تشخیص و لاگ درخواست‌های مشکوک"""
        path = request.path.lower()
        query = request.GET.urlencode().lower()
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        client_ip = self._get_client_ip(request)
        
        # بررسی الگوهای مشکوک
        for pattern, attack_type in self._suspicious_patterns:
            if re.search(pattern, path) or re.search(pattern, query):
                self._logger.warning(
                    f'🚨 Suspicious request detected: {attack_type} - '
                    f'{request.method} {request.path} '
                    f'from {client_ip} '
                    f'UA: {user_agent[:50]}'
                )
                break

    def _get_client_ip(self, request):
        """دریافت IP کاربر"""
        cf_connecting_ip = request.META.get('HTTP_CF_CONNECTING_IP')
        if cf_connecting_ip:
            return cf_connecting_ip
        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')

    def _log_security_event(self, request, response):
        """لاگ رویدادهای امنیتی"""
        client_ip = self._get_client_ip(request)
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        
        self._logger.info(
            f'🔒 Security event: {response.status_code} '
            f'{request.method} {request.path} '
            f'User: {user_id} from {client_ip}'
        )


# ============================================================
# WhiteNoise Middleware (فیکس شده - با پشتیبانی از فایل‌های بزرگ)
# ============================================================

class WhiteNoiseMiddleware(MiddlewareMixin):
    """
    Middleware سفارشی برای مدیریت فایل‌های استاتیک با کش هوشمند
    """
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        self._static_url = settings.STATIC_URL
        self._media_url = settings.MEDIA_URL
        self._cache_duration = getattr(settings, 'WHITENOISE_CACHE_DURATION', 31536000)  # 1 سال
        
        # تنظیمات کش
        self._cache_control = {
            'static': f'public, max-age={self._cache_duration}, immutable',
            'media': 'public, max-age=86400',  # 24 ساعت
            'no_cache': 'no-cache, no-store, must-revalidate'
        }

    def __call__(self, request):
        response = self.get_response(request)
        
        # مدیریت کش برای فایل‌های استاتیک و رسانه
        path = request.path
        
        if path.startswith(self._static_url):
            self._add_cache_headers(response, 'static')
        elif path.startswith(self._media_url):
            self._add_cache_headers(response, 'media')
        else:
            # برای سایر مسیرها
            if not self._should_cache(request):
                self._add_cache_headers(response, 'no_cache')
        
        return response

    def _add_cache_headers(self, response, cache_type):
        """افزودن هدرهای کش مناسب - فیکس شده"""
        if cache_type in self._cache_control:
            response['Cache-Control'] = self._cache_control[cache_type]
            
        # ✅ افزودن ETag فقط برای فایل‌های کوچک
        if cache_type in ['static', 'media']:
            if hasattr(response, 'content') and len(response.content) < 10 * 1024 * 1024:  # < 10MB
                import hashlib
                etag = hashlib.md5(response.content).hexdigest()
                response['ETag'] = f'"{etag}"'
            elif hasattr(response, 'streaming_content'):
                # ✅ برای فایل‌های بزرگ، از ETag استفاده نکن
                pass

    def _should_cache(self, request):
        """بررسی اینکه آیا پاسخ باید کش شود"""
        # برای درخواست‌های POST و غیره کش نکن
        if request.method not in ['GET', 'HEAD']:
            return False
        
        # برای کاربران احراز هویت شده کش نکن
        if request.user.is_authenticated:
            return False
        
        return True


# ============================================================
# Performance Monitoring Middleware (فیکس شده)
# ============================================================

class PerformanceMiddleware(MiddlewareMixin):
    """
    مانیتورینگ عملکرد و زمان پاسخگویی
    """
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        self._logger = logging.getLogger('performance')
        self._slow_threshold = getattr(settings, 'SLOW_REQUEST_THRESHOLD', 1.0)  # ثانیه
        self._exempt_paths = getattr(settings, 'PERFORMANCE_EXEMPT_PATHS', [])

    def __call__(self, request):
        import time
        start_time = time.time()
        
        response = self.get_response(request)
        
        duration = time.time() - start_time
        
        # ✅ اضافه کردن هدر زمان پاسخگویی فقط در DEBUG
        if settings.DEBUG:
            response['X-Response-Time'] = f'{duration:.3f}s'
        
        # ✅ لاگ درخواست‌های کند
        if duration > self._slow_threshold and not self._is_exempt(request.path):
            self._logger.warning(
                f'🐢 Slow request: {duration:.2f}s - '
                f'{request.method} {request.path} '
                f'from {request.META.get("REMOTE_ADDR")}'
            )
        
        return response

    def _is_exempt(self, path):
        """بررسی مسیرهای معاف از لاگ"""
        for exempt_path in self._exempt_paths:
            if path.startswith(exempt_path):
                return True
        return False


# ============================================================
# Configuration Helper
# ============================================================

def setup_security_middleware():
    """
    راهنمای تنظیم middlewareها در settings.py
    """
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║     🚀 راهنمای تنظیم Middlewareهای امنیتی                ║
    ╚══════════════════════════════════════════════════════════╝
    
    در فایل settings.py خود، middlewareهای زیر را به ترتیب اضافه کنید:
    
    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'whitenoise.middleware.WhiteNoiseMiddleware',  # اگر از whitenoise استفاده می‌کنید
        'your_app.middleware.PerformanceMiddleware',
        'your_app.middleware.WhiteNoiseMiddleware',  # سفارشی
        'your_app.middleware.SecurityHeadersMiddleware',
        'your_app.middleware.RateLimitMiddleware',
        'your_app.middleware.SecurityLoggingMiddleware',
        # ... سایر middlewareهای Django
    ]
    
    📋 تنظیمات مورد نیاز:
    
    # ===== تنظیمات CSP =====
    CSP_EXTRA_DOMAINS = [
        'https://example.com',
        'https://cdn.example.com',
    ]
    
    CSP_API_DOMAINS = [
        'https://api.example.com',
    ]
    
    CSP_WEBSOCKET_DOMAINS = [
        'wss://ws.example.com',
    ]
    
    CSP_UNSAFE_INLINE = False  # برای Production = False
    
    # ===== تنظیمات Rate Limit =====
    RATE_LIMIT_PER_MINUTE = 60  # تعداد درخواست در دقیقه
    RATE_LIMIT_EXEMPT_PATHS = [
        '/admin/',
        '/api/webhook/',
    ]
    RATE_LIMIT_USE_CACHE = True  # استفاده از Cache
    
    # ===== تنظیمات کش =====
    WHITENOISE_CACHE_DURATION = 31536000  # 1 سال
    
    # ===== تنظیمات عملکرد =====
    SLOW_REQUEST_THRESHOLD = 1.0  # ثانیه
    PERFORMANCE_EXEMPT_PATHS = [
        '/static/',
        '/media/',
    ]
    
    # ===== تنظیمات لاگ =====
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'file': {
                'level': 'INFO',
                'class': 'logging.FileHandler',
                'filename': 'logs/security.log',
            },
            'performance_file': {
                'level': 'INFO',
                'class': 'logging.FileHandler',
                'filename': 'logs/performance.log',
            },
        },
        'loggers': {
            'security': {
                'handlers': ['file'],
                'level': 'INFO',
                'propagate': True,
            },
            'performance': {
                'handlers': ['performance_file'],
                'level': 'INFO',
                'propagate': True,
            },
            'security.ratelimit': {
                'handlers': ['file'],
                'level': 'WARNING',
                'propagate': True,
            },
        },
    }
    
    ⚠️ نکات مهم:
    1. برای Production، حتماً CSP_UNSAFE_INLINE را False کنید
    2. از Cache backend (Redis/Memcached) برای Rate Limit استفاده کنید
    3. لاگ‌ها را به صورت دورانی (rotating) تنظیم کنید
    4. از CDN برای فایل‌های استاتیک استفاده کنید
    """)