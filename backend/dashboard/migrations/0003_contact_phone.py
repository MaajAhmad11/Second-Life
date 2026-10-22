from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0002_platformsetting'),
    ]

    operations = [
        migrations.AddField(
            model_name='contactmessage',
            name='country_code',
            field=models.CharField(blank=True, default='', max_length=8),
        ),
        migrations.AddField(
            model_name='contactmessage',
            name='phone_number',
            field=models.CharField(blank=True, default='', max_length=32),
        ),
    ]
