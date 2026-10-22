from rest_framework import serializers
import phonenumbers
from phonenumbers import NumberParseException
from dashboard.models import ActivityLog, ContactMessage

class ActivityLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', default='System', read_only=True)
    user_role = serializers.CharField(source='user.role', default='SYSTEM', read_only=True)

    class Meta:
        model = ActivityLog
        fields = ['id', 'user_name', 'user_role', 'action', 'description', 'ip_address', 'created_at']

class ContactMessageSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        phone = str(attrs.get('phone_number', '') or '').strip()
        country = str(attrs.get('country_code', '') or '').upper()

        if phone:
            try:
                parsed = phonenumbers.parse(phone, None if phone.startswith('+') else country or None)
            except NumberParseException:
                raise serializers.ValidationError({
                    'phone_number': 'Please enter a valid phone number.'
                })

            if not phonenumbers.is_possible_number(parsed) or not phonenumbers.is_valid_number(parsed):
                raise serializers.ValidationError({
                    'phone_number': 'Please enter a valid phone number.'
                })

            attrs['phone_number'] = phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )

            # Keep the selected ISO country for admin display.
            if not country:
                attrs['country_code'] = phonenumbers.region_code_for_number(parsed) or ''

        return attrs

    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'subject', 'country_code', 'phone_number', 'message', 'is_resolved', 'admin_notes', 'created_at']
        read_only_fields = ['id', 'is_resolved', 'created_at']
