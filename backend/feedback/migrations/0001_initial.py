from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('accounts','0001_initial'),('connections','0002_live_locations')]
    operations = [
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveSmallIntegerField(default=5)),
                ('comment', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feedback_given', to='accounts.user')),
                ('connection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feedback', to='connections.connection')),
            ],
            options={'ordering': ['-created_at'], 'unique_together': {('connection','author')}},
        ),
    ]
