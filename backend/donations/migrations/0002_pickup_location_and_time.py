from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies=[('donations','0001_initial')]
    operations=[
        migrations.AddField(model_name='donation',name='pickup_date',field=models.CharField(max_length=100,blank=True,default='')),
        migrations.AddField(model_name='donation',name='pickup_time',field=models.CharField(max_length=100,blank=True,default='')),
        migrations.AddField(model_name='donation',name='pickup_latitude',field=models.DecimalField(max_digits=10,decimal_places=7,null=True,blank=True)),
        migrations.AddField(model_name='donation',name='pickup_longitude',field=models.DecimalField(max_digits=10,decimal_places=7,null=True,blank=True)),
    ]
