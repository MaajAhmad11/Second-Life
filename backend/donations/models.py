from django.db import models
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, blank=True, default='package') # lucide icon name
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

class Donation(models.Model):
    class Condition(models.TextChoices):
        NEW = 'NEW', 'New (In original packaging)'
        LIKE_NEW = 'LIKE_NEW', 'Like New (Barely used)'
        GOOD = 'GOOD', 'Good (Visible wear, fully functional)'
        FAIR = 'FAIR', 'Fair (Significant wear, needs minor repair)'

    class DeliveryOption(models.TextChoices):
        PICKUP = 'PICKUP', 'Pickup Available'
        DELIVERY = 'DELIVERY', 'Delivery Preferred'
        EITHER = 'EITHER', 'Pickup or Delivery'

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        AVAILABLE = 'AVAILABLE', 'Available'
        PENDING = 'PENDING', 'Pending Match'
        MATCHED = 'MATCHED', 'Matched'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        IN_DELIVERY = 'IN_DELIVERY', 'In Delivery'
        DELIVERED = 'DELIVERED', 'Delivered'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='donations')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='donations')
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    condition = models.CharField(max_length=20, choices=Condition.choices, default=Condition.GOOD)
    quantity = models.PositiveIntegerField(default=1)
    delivery_option = models.CharField(max_length=20, choices=DeliveryOption.choices, default=DeliveryOption.PICKUP)
    location = models.CharField(max_length=255, help_text="e.g. Ballard, Seattle, WA")
    city = models.CharField(max_length=100, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE, db_index=True)
    dimensions = models.CharField(max_length=100, blank=True, default='')
    weight = models.CharField(max_length=100, blank=True, default='')
    pickup_date = models.CharField(max_length=100, blank=True, default='')
    pickup_time = models.CharField(max_length=100, blank=True, default='')
    pickup_latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    pickup_longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'category']),
            models.Index(fields=['city', 'status']),
        ]

    def __str__(self):
        return f"{self.title} ({self.status})"

    @property
    def weight_kg(self):
        import re
        if not self.weight:
            return None
        match = re.search(r'([-+]?\d+(?:\.\d+)?)\s*(kg|kgs|kilograms?|lb|lbs|pounds?)?', str(self.weight).lower())
        if not match:
            return None
        value = float(match.group(1))
        unit = (match.group(2) or 'kg').lower()
        if unit.startswith('lb') or unit.startswith('pound'):
            value *= 0.45359237
        return round(value, 3)

    @property
    def total_weight_kg(self):
        """Return the total weight represented by this donation quantity."""
        unit_weight = self.weight_kg
        if unit_weight is None:
            return None
        return round(unit_weight * max(int(self.quantity or 1), 1), 3)

    @property
    def primary_image_url(self):
        primary = self.images.filter(is_primary=True).first() or self.images.first()
        if primary:
            if primary.image:
                return primary.image.url
            if primary.image_url:
                return primary.image_url
        return None

class DonationImage(models.Model):
    donation = models.ForeignKey(Donation, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='donations/', blank=True, null=True)
    image_url = models.CharField(max_length=500, blank=True, default='')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_primary', 'id']

    def __str__(self):
        return f"Image for {self.donation.title}"

class SavedItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_items')
    donation = models.ForeignKey(Donation, on_delete=models.CASCADE, related_name='saved_by_users')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'donation')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.name} saved {self.donation.title}"
