from django.urls import path
from . import views

app_name = 'server1'  # ✅ تغییر از 'server' به 'server1'

urlpatterns = [
    # صفحه اصلی وضعیت سرور
    path('status/', views.server_status, name='server_status'),
    
    # API برای دریافت داده‌ها (AJAX)
    path('api/status/', views.server_status_json, name='server_status_json'),
    
    # API برای پلیرهای آنلاین (نسخه سبک)
    path('api/online-players/', views.online_players_json, name='online_players_json'),
]