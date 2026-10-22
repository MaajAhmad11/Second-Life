from django.db import models
from django.conf import settings
from donations.models import Donation
from item_requests.models import DonationRequest

class Connection(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Schedule'
        ACCEPTED = 'ACCEPTED', 'Schedule Confirmed'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress / Transit'
        DELIVERED = 'DELIVERED', 'Delivered / Handed Over'
        COMPLETED = 'COMPLETED', 'Completed & Impact Recorded'
        CANCELLED = 'CANCELLED', 'Cancelled'

    donation = models.ForeignKey(Donation, on_delete=models.CASCADE, related_name='connections')
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='donor_connections')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='receiver_connections')
    request = models.OneToOneField(DonationRequest, on_delete=models.CASCADE, related_name='connection')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACCEPTED, db_index=True)
    scheduled_date = models.CharField(max_length=100, blank=True, default='Tomorrow, 10:00 AM')
    pickup_time_slot = models.CharField(max_length=100, blank=True, default='10:00 AM - 12:00 PM')
    pickup_address = models.CharField(max_length=255, blank=True, default='')
    courier_notes = models.TextField(blank=True, default='')
    donor_live_latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    donor_live_longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    donor_live_address = models.CharField(max_length=500, blank=True, default='')
    receiver_live_latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    receiver_live_longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    receiver_live_address = models.CharField(max_length=500, blank=True, default='')
    location_shared_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Connection: {self.donor.name} -> {self.receiver.name} for {self.donation.title} ({self.status})"

class Delivery(models.Model):
    class DeliveryStatus(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Pickup Scheduled'
        PROCESSING = 'PROCESSING', 'Processing'
        TRANSIT = 'TRANSIT', 'In Transit'
        ARRIVING = 'ARRIVING', 'Driver Arriving Soon'
        DELIVERED = 'DELIVERED', 'Delivered'

    connection = models.OneToOneField(Connection, on_delete=models.CASCADE, related_name='delivery')
    tracking_code = models.CharField(max_length=50, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=DeliveryStatus.choices, default=DeliveryStatus.SCHEDULED)
    courier_name = models.CharField(max_length=100, default='SecondLife Eco Courier')
    courier_phone = models.CharField(max_length=50, default='+1 (555) 019-2831')
    vehicle_info = models.CharField(max_length=100, default='Green Electric Van #SL-402')
    estimated_arrival = models.CharField(max_length=100, default='Today, 2:30 PM - 4:00 PM')
    timeline_steps = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Delivery {self.tracking_code} ({self.status})"
