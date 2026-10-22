from rest_framework import serializers
from organizations.models import Organization, OrganizationVerification

class OrganizationVerificationLogSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source='reviewed_by.name', read_only=True)

    class Meta:
        model = OrganizationVerification
        fields = ['id', 'reviewer_name', 'action', 'notes', 'created_at']

class OrganizationSerializer(serializers.ModelSerializer):
    verifications = OrganizationVerificationLogSerializer(many=True, read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_role = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = Organization
        fields = [
            'id', 'user_name', 'user_email', 'user_role', 'organization_name',
            'organization_type', 'license_number', 'contact_person', 'official_email',
            'phone', 'address', 'city', 'country', 'website', 'description',
            'verification_status', 'verification_reason', 'verified_at',
            'verifications', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'verification_status', 'verification_reason', 'verified_at', 'created_at', 'updated_at']

class OrganizationReviewSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['VERIFIED', 'REJECTED'])
    notes = serializers.CharField(required=False, allow_blank=True, default='')
