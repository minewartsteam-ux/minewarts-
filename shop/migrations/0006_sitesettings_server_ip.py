from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0005_add_sitesettings_color_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='server_ip',
            field=models.CharField(blank=True, help_text='آی‌پی یا دامنه سرور که در صفحه اصلی نمایش می‌شود', max_length=100, null=True, verbose_name='آی‌پی سرور'),
        ),
    ]




