# Generated manually to fix missing fields in SiteSettings

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0004_product_has_monthly_options_productmonth'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='primary_color',
            field=models.CharField(default='#4CAF50', help_text='مثال: #4CAF50', max_length=20, verbose_name='رنگ اصلی (primary)'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='secondary_color',
            field=models.CharField(default='#FFC107', help_text='مثال: #FFC107', max_length=20, verbose_name='رنگ ثانویه (secondary)'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='accent_color',
            field=models.CharField(default='#03A9F4', help_text='مثال: #03A9F4', max_length=20, verbose_name='رنگ تأکیدی (accent)'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='dark_bg_color',
            field=models.CharField(default='#121212', help_text='پس\u200cزمینه کلی سایت (body)', max_length=20, verbose_name='رنگ پس\u200cزمینه تیره'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='card_bg_color',
            field=models.CharField(default='rgba(30, 30, 30, 0.85)', help_text='مثال: rgba(30, 30, 30, 0.85)', max_length=50, verbose_name='رنگ پس\u200cزمینه کارت\u200cها'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='text_light_color',
            field=models.CharField(default='#E0E0E0', help_text='مثال: #E0E0E0', max_length=20, verbose_name='رنگ متن اصلی'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='text_muted_color',
            field=models.CharField(default='#9E9E9E', help_text='مثال: #9E9E9E', max_length=20, verbose_name='رنگ متن کم\u200cرنگ'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='navbar_title',
            field=models.CharField(blank=True, help_text='اگر خالی باشد از نام سایت استفاده می\u200cشود', max_length=200, null=True, verbose_name='عنوان نوار بالا (Navbar)'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='footer_text',
            field=models.CharField(default='© 2024 فروشگاه ماینکرفت - ساخته شده با ❤️ و Django', help_text='متنی که در پایین تمام صفحات نمایش داده می\u200cشود', max_length=300, verbose_name='متن فوتر'),
        ),
    ]
