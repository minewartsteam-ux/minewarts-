from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('verify/<uidb64>/<token>/', views.verify_email, name='verify_email'),
    path('verify-code/', views.verify_code_view, name='verify_code'),
    path('resend-code/', views.resend_code_view, name='resend_code'),  # ✅ مهم
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('tickets/', views.ticket_list, name='ticket_list'),
    path('tickets/create/', views.ticket_create, name='ticket_create'),
    path('tickets/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('support-panel/', views.support_panel_dashboard, name='support_panel_dashboard'),
    path('support-panel/tickets/<int:ticket_id>/', views.support_panel_ticket_detail, name='support_panel_ticket_detail'),
    path('wart-coin/balance/', views.wart_coin_balance_api, name='wart_coin_balance_api'),
    path('wart-coin/buy/', views.buy_wart_coins_view, name='buy_wart_coins'),
    path('wart-coin/price/', views.get_wart_coin_price_api, name='wart_coin_price_api'),
    path('wart-coin/leaderboard/', views.wart_coin_leaderboard, name='wart_coin_leaderboard'),
    path('more-info/', views.more_info_view, name='more_info'),
    path('admin-info/', views.admin_info_view, name='admin_info'),
]