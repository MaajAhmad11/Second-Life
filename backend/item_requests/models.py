from django.db import models
from django.conf import settings
from donations.models import Donation

class DonationRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Review'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        CANCELLED = 'CANCELLED', 'Cancelled'
        MATCHED = 'MATCHED', 'Matched'
        COMPLETED = 'COMPLETED', 'Completed'

    donation = models.ForeignKey(Donation, on_delete=models.CASCADE, related_name='requests')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='item_requests')
    message = models.TextField(help_text="Reason for request and intended usage")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    rejection_reason = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'receiver']),
            models.Index(fields=['donation', 'status']),
        ]

    def __str__(self):
        return f"Request by {self.receiver.name} for {self.donation.title} ({self.status})"
