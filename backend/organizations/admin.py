from django.contrib import admin
from organizations.models import Organization, OrganizationVerification

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('organization_name', 'organization_type', 'contact_person', 'official_email', 'city', 'verification_status', 'created_at')
    list_filter = ('verification_status', 'organization_type', 'city')
    search_fields = ('organization_name', 'contact_person', 'license_number', 'official_email')
    ordering = ('-created_at',)

@admin.register(OrganizationVerification)
class OrganizationVerificationAdmin(admin.ModelAdmin):
    list_display = ('organization', 'reviewed_by', 'action', 'created_at')
    list_filter = ('action',)
    search_fields = ('organization__organization_name', 'reviewed_by__name')
