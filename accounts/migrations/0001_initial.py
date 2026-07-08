# Generated manually for SupportTicket and SupportMessage models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SupportTicket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=255, verbose_name='موضوع')),
                ('status', models.CharField(choices=[('open', 'باز'), ('answered', 'پاسخ‌داده‌شده'), ('closed', 'بسته شده')], default='open', max_length=20, verbose_name='وضعیت')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')),
                ('assigned_admins', models.ManyToManyField(blank=True, help_text='کاربرانی که می‌توانند به این تیکت پاسخ دهند', related_name='assigned_tickets', to=settings.AUTH_USER_MODEL, verbose_name='ادمین‌های اختصاص‌یافته')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='support_tickets', to=settings.AUTH_USER_MODEL, verbose_name='کاربر')),
            ],
            options={
                'verbose_name': 'تیکت پشتیبانی',
                'verbose_name_plural': 'تیکت‌های پشتیبانی',
                'ordering': ['-updated'],
            },
        ),
        migrations.CreateModel(
            name='SupportMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_staff', models.BooleanField(default=False, verbose_name='پیام از طرف پشتیبانی')),
                ('message', models.TextField(verbose_name='متن پیام')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ارسال')),
                ('sender', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='support_messages', to=settings.AUTH_USER_MODEL, verbose_name='فرستنده')),
                ('ticket', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='accounts.supportticket', verbose_name='تیکت')),
            ],
            options={
                'verbose_name': 'پیام تیکت',
                'verbose_name_plural': 'پیام‌های تیکت',
                'ordering': ['created'],
            },
        ),
    ]
