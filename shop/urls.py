from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('category/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    # آدرس محصولات را به product/ تغییر دادیم تا با آدرس‌های دیگر تداخل نداشته باشد
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('product/<slug:slug>/specifications/', views.product_specifications, name='product_specifications'),
    path('product/<slug:slug>/monthly-options/', views.product_monthly_options, name='product_monthly_options'),
    path('server-ip/', views.server_ip_view, name='server_ip'),
]
from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('category/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('product/<slug:slug>/monthly/', views.product_monthly_options, name='product_monthly_options'),
    path('product/<slug:slug>/specifications/', views.product_specifications, name='product_specifications'),
    path('server-ip/', views.server_ip_view, name='server_ip'),
]