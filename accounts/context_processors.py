"""
Context processor برای بررسی دسترسی کاربران به پنل پشتیبانی
"""
from .models import SupportTicket


def user_ticket_access(request):
    """
    بررسی اینکه آیا کاربر به پنل پشتیبانی دسترسی دارد
    """
    user_has_assigned_tickets = False
    
    if request.user.is_authenticated:
        if request.user.is_staff:
            user_has_assigned_tickets = True
        else:
            try:
                user_has_assigned_tickets = SupportTicket.objects.filter(assigned_admins=request.user).exists()
            except (AttributeError, Exception):
                user_has_assigned_tickets = False
    
    return {
        'user_has_assigned_tickets': user_has_assigned_tickets,
    }
