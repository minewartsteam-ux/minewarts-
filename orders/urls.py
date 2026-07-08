from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('create/', views.order_create, name='order_create'),
    path('payment/<int:order_id>/', views.payment, name='payment'),
    path('payment/success/<int:order_id>/', views.payment_success, name='payment_success'),
    path('payment/wart-coin/<int:purchase_id>/', views.payment_wart_coin, name='payment_wart_coin'),
    path('payment/wart-coin/callback/<int:purchase_id>/', views.payment_wart_coin_callback, name='payment_wart_coin_callback'),
    path('detail/<int:order_id>/', views.order_detail, name='order_detail'),
]