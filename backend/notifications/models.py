from django.db import models
from django.conf import settings

class Notification(models.Model):
    class NotificationType(models.TextChoices):
        REGISTRATION = 'REGISTRATION', 'Registration'
        VERIFICATION = 'VERIFICATION', 'Organization Verification'
        DONATION_CREATED = 'DONATION_CREATED', 'Donation Created'
        REQUEST_RECEIVED = 'REQUEST_RECEIVED', 'Request Received'
        REQUEST_APPROVED = 'REQUEST_APPROVED', 'Request Approved'
        REQUEST_REJECTED = 'REQUEST_REJECTED', 'Request Rejected'
        CONNECTION_CREATED = 'CONNECTION_CREATED', 'Connection Created'
        DELIVERY_UPDATE = 'DELIVERY_UPDATE', 'Delivery Update'
        DONATION_DELIVERED = 'DONATION_DELIVERED', 'Donation Delivered'
        SYSTEM = 'SYSTEM', 'System'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    type = models.CharField(max_length=30, choices=NotificationType.choices, default=NotificationType.SYSTEM)
    is_read = models.BooleanField(default=False, db_index=True)
    link = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.name}: {self.title}"
