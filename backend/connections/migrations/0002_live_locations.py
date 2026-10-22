from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies=[('connections','0001_initial')]
    operations=[
        migrations.AddField(model_name='connection',name='donor_live_latitude',field=models.DecimalField(max_digits=10,decimal_places=7,null=True,blank=True)),
        migrations.AddField(model_name='connection',name='donor_live_longitude',field=models.DecimalField(max_digits=10,decimal_places=7,null=True,blank=True)),
        migrations.AddField(model_name='connection',name='donor_live_address',field=models.CharField(max_length=500,blank=True,default='')),
        migrations.AddField(model_name='connection',name='receiver_live_latitude',field=models.DecimalField(max_digits=10,decimal_places=7,null=True,blank=True)),
        migrations.AddField(model_name='connection',name='receiver_live_longitude',field=models.DecimalField(max_digits=10,decimal_places=7,null=True,blank=True)),
        migrations.AddField(model_name='connection',name='receiver_live_address',field=models.CharField(max_length=500,blank=True,default='')),
        migrations.AddField(model_name='connection',name='location_shared_at',field=models.DateTimeField(null=True,blank=True)),
    ]
