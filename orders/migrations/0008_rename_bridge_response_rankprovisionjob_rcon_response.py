from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0007_rankprovisionjob'),
    ]

    operations = [
        migrations.RenameField(
            model_name='rankprovisionjob',
            old_name='bridge_response',
            new_name='rcon_response',
        ),
    ]
