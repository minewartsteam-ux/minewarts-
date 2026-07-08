# signals.py
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from .models import WartCoin

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_wallet(sender, instance, created, **kwargs):
    if created:
        WartCoin.objects.create(
            user=instance,
            balance=100.00  # 🎁 100 وارت کوین هدیه ثبت‌نام
        )