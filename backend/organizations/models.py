from django.db import models
from django.conf import settings

class Organization(models.Model):
    class VerificationStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        VERIFIED = 'VERIFIED', 'Verified'
        REJECTED = 'REJECTED', 'Rejected'

    class OrgType(models.TextChoices):
        NGO = 'NGO', 'Non-Profit / NGO'
        CHARITY = 'CHARITY', 'Charity Organization'
        SCHOOL = 'SCHOOL', 'Educational Institution'
        COMMUNITY = 'COMMUNITY', 'Community Center'
        SHELTER = 'SHELTER', 'Shelter / Relief Camp'
        FOUNDATION = 'FOUNDATION', 'Foundation'
        RELIGIOUS = 'RELIGIOUS', 'Faith-Based Organization'
        OTHER = 'OTHER', 'Other'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='organization')
    organization_name = models.CharField(max_length=255, db_index=True)
    organization_type = models.CharField(max_length=50, choices=OrgType.choices, default=OrgType.NGO)
    license_number = models.CharField(max_length=100, blank=True, default='')
    contact_person = models.CharField(max_length=255)
    official_email = models.EmailField()
    phone = models.CharField(max_length=30)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100, db_index=True)
    country = models.CharField(max_length=100, default='USA')
    website = models.URLField(blank=True, default='')
    description = models.TextField(blank=True, default='')
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        db_index=True
    )
    verification_reason = models.TextField(blank=True, default='')
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.organization_name} ({self.verification_status})"

class OrganizationVerification(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='verifications')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='reviewed_verifications')
    action = models.CharField(max_length=20, choices=[('VERIFIED', 'Verified'), ('REJECTED', 'Rejected')])
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.organization.organization_name} -> {self.action} on {self.created_at.strftime('%Y-%m-%d')}"
