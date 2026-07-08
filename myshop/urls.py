from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from shop.views import admin_dashboard

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    
    # Apps
    path('accounts/', include('accounts.urls')),
    path('cart/', include('cart.urls')),
    path('orders/', include('orders.urls')),
    path('', include('shop.urls')),
    
    # Server app - ✅ مسیر کامل را مشخص کنید
    path('server/', include('myshop.server.urls', namespace='server')),
    path('__debug__/', include('debug_toolbar.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)