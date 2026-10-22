from django.db import models
from django.conf import settings
from connections.models import Connection
class Feedback(models.Model):
    connection=models.ForeignKey(Connection,on_delete=models.CASCADE,related_name='feedback')
    author=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='feedback_given')
    rating=models.PositiveSmallIntegerField(default=5)
    comment=models.TextField(blank=True,default='')
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together=('connection','author')
        ordering=['-created_at']
