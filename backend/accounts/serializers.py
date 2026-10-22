from django.db import IntegrityError
from rest_framework import serializers
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
import re

import phonenumbers
from phonenumbers import NumberParseException

from accounts.models import Profile
from organizations.models import Organization
from dashboard.models import ActivityLog
from services.notification_service import NotificationService


User = get_user_model()


# ============================================================
# PROFILE
# ============================================================

class ProfileSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'image',
            'bio',
            'preferred_categories',
            'needed_categories',
            'pickup_radius',
            'latitude',
            'longitude',
            'handover_preference',
            'updated_at',
        ]

    def get_image(self, obj):
        request = self.context.get('request')

        if not obj.image:
            return None

        try:
            url = obj.image.url
        except ValueError:
            return None

        # Cache-bust profile images when the profile is updated so the
        # newest avatar is restored immediately after refresh/login.
        version = obj.updated_at.timestamp() if obj.updated_at else ''
        separator = '&' if '?' in url else '?'
        url = f'{url}{separator}v={version}' if version else url

        if request and url.startswith('/'):
            return request.build_absolute_uri(url)

        return url


# ============================================================
# ORGANIZATION
# ============================================================

class UserOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            'id',
            'organization_name',
            'organization_type',
            'license_number',
            'contact_person',
            'official_email',
            'phone',
            'address',
            'city',
            'website',
            'description',
            'verification_status',
            'verification_reason',
            'verified_at',
        ]


# ============================================================
# USER
# ============================================================

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    organization = UserOrganizationSerializer(read_only=True)
    initials = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'name',
            'phone',
            'role',
            'account_type',
            'address',
            'city',
            'country',
            'is_verified',
            'is_active',
            'initials',
            'profile',
            'organization',
            'created_at',
        ]

        read_only_fields = [
            'id',
            'role',
            'account_type',
            'is_verified',
            'is_active',
            'created_at',
        ]


# ============================================================
# REGISTER
# ============================================================

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8
    )

    confirm_password = serializers.CharField(
        write_only=True,
        required=True
    )

    phone_country = serializers.CharField(
        write_only=True,
        required=False,
        default='PK',
        max_length=2,
    )

    organization_name = serializers.CharField(
        required=False,
        allow_blank=True
    )

    organization_type = serializers.CharField(
        required=False,
        allow_blank=True
    )

    license_number = serializers.CharField(
        required=False,
        allow_blank=True
    )

    website = serializers.CharField(
        required=False,
        allow_blank=True
    )

    org_description = serializers.CharField(
        required=False,
        allow_blank=True
    )

    preferred_categories = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )

    needed_categories = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )

    class Meta:
        model = User
        fields = [
            'email',
            'password',
            'confirm_password',
            'name',
            'phone',
            'phone_country',
            'role',
            'account_type',
            'address',
            'city',
            'country',
            'organization_name',
            'organization_type',
            'license_number',
            'website',
            'org_description',
            'preferred_categories',
            'needed_categories',
        ]

    def validate_name(self, value):
        value = ' '.join(str(value or '').split())
        if not value or len(value) < 2 or len(value) > 100:
            raise serializers.ValidationError('Enter a name between 2 and 100 characters.')
        # Unicode letters and combining marks are accepted; spaces, apostrophes,
        # hyphens, and periods are allowed for legitimate international names.
        if not re.fullmatch(r"[\\w\\u0300-\\u036f .'-]+", value, flags=re.UNICODE) or any(ch.isdigit() or ch == '_' for ch in value):
            raise serializers.ValidationError('Name may contain letters, spaces, apostrophes, hyphens, and periods only.')
        return value

    def validate_address(self, value):
        value = ' '.join(str(value or '').split())
        if len(value) < 4 or len(value) > 255 or not any(ch.isalnum() for ch in value):
            raise serializers.ValidationError('Enter a valid address between 4 and 255 characters.')
        return value

    def validate_email(self, value):
        email = value.strip().lower()

        # Strong, user-facing email checks before an OTP is generated.
        if len(email) > 254 or email.count('@') != 1:
            raise serializers.ValidationError('Please enter a valid email address.')

        local, domain = email.rsplit('@', 1)
        if not local or len(local) > 64 or not domain:
            raise serializers.ValidationError('Please enter a valid email address.')

        if (
            local.startswith('.')
            or local.endswith('.')
            or '..' in local
            or domain.startswith('.')
            or domain.endswith('.')
            or '..' in domain
        ):
            raise serializers.ValidationError('Please enter a valid email address.')

        if not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+", local):
            raise serializers.ValidationError('Please enter a valid email address.')

        # Second Life registration requires a public domain-style address.
        # Reject placeholder/fake-looking numeric addresses such as 123@123.com
        # before an OTP is generated. This is a product validation rule; it does
        # not claim that an address actually has a working mailbox.
        if re.fullmatch(r'\d+', local):
            raise serializers.ValidationError('Please enter a valid email address.')

        labels = domain.split('.')
        if len(labels) < 2 or any(
            not label
            or len(label) > 63
            or label.startswith('-')
            or label.endswith('-')
            or not re.fullmatch(r'[A-Za-z0-9-]+', label)
            for label in labels
        ):
            raise serializers.ValidationError('Please enter a valid email address.')

        tld = labels[-1]
        if (
            not re.fullmatch(r'[A-Za-z]{2,63}', tld)
            or not re.search(r'[A-Za-z]', labels[0])
        ):
            raise serializers.ValidationError('Please enter a valid email address.')

        try:
            validate_email(email)
        except ValidationError:
            raise serializers.ValidationError('Please enter a valid email address.')

        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                "This email is already registered."
            )

        return email

    def validate_phone(self, value):
        phone = str(value or '').strip()
        country = str(self.initial_data.get('phone_country') or 'PK').upper()

        if not re.fullmatch(r'[+0-9() .-]+', phone):
            raise serializers.ValidationError('Please enter a valid phone number.')

        if not re.fullmatch(r'[A-Z]{2}', country):
            raise serializers.ValidationError('Please select a valid country calling code.')

        try:
            parsed = phonenumbers.parse(phone, None if phone.startswith('+') else country)
        except NumberParseException:
            raise serializers.ValidationError('Please enter a valid phone number.')

        if not phonenumbers.is_possible_number(parsed) or not phonenumbers.is_valid_number(parsed):
            raise serializers.ValidationError('Please enter a valid phone number for the selected country.')

        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters."
            )

        if not any(char.isupper() for char in value):
            raise serializers.ValidationError(
                "Password must contain at least one uppercase letter."
            )

        if not any(char.islower() for char in value):
            raise serializers.ValidationError(
                "Password must contain at least one lowercase letter."
            )

        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError(
                "Password must contain at least one digit."
            )

        if not any(
            not char.isalnum()
            for char in value
        ):
            raise serializers.ValidationError(
                "Password must contain at least one special character."
            )

        return value

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')

        if password != confirm_password:
            raise serializers.ValidationError({
                "password": "Passwords do not match."
            })

        if (
            attrs.get('account_type') ==
            User.AccountType.ORGANIZATION
            and not attrs.get(
                'organization_name',
                ''
            ).strip()
        ):
            raise serializers.ValidationError({
                "organization_name":
                    "Organization name is required for organization accounts."
            })

        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        validated_data.pop('phone_country', None)

        org_name = validated_data.pop(
            'organization_name',
            ''
        )

        org_type = validated_data.pop(
            'organization_type',
            'NGO'
        )

        license_num = validated_data.pop(
            'license_number',
            ''
        )

        website = validated_data.pop(
            'website',
            ''
        )

        org_desc = validated_data.pop(
            'org_description',
            ''
        )

        preferred_cats = validated_data.pop(
            'preferred_categories',
            []
        )

        needed_cats = validated_data.pop(
            'needed_categories',
            []
        )

        password = validated_data.pop('password')

        account_type = validated_data.get(
            'account_type',
            User.AccountType.INDIVIDUAL
        )

        is_verified = (
            account_type == User.AccountType.INDIVIDUAL
        )

        try:
            user = User.objects.create_user(
                password=password,
                is_verified=is_verified,
                **validated_data
            )

        except IntegrityError:
            raise serializers.ValidationError({
                "email": "This email is already registered."
            })

        Profile.objects.create(
            user=user,
            preferred_categories=preferred_cats,
            needed_categories=needed_cats
        )

        if (
            account_type ==
            User.AccountType.ORGANIZATION
        ):
            organization = Organization.objects.create(
                user=user,
                organization_name=(
                    org_name or user.name
                ),
                organization_type=(
                    org_type or 'NGO'
                ),
                license_number=license_num,
                contact_person=user.name,
                official_email=user.email,
                phone=user.phone,
                address=user.address,
                city=user.city,
                country=user.country,
                website=website,
                description=org_desc,
                verification_status=(
                    Organization.VerificationStatus.PENDING
                )
            )
            # Send only after the registration transaction commits. A mail
            # provider outage must not undo a valid registration.
            from django.db import transaction
            from services.email_service import send_platform_email
            from django.utils import timezone
            org_email = (
                f"A new organization has submitted a registration request on Second Life.\\n\\n"
                f"Organization: {organization.organization_name}\\n"
                f"Contact Email: {organization.official_email}\\n"
                f"Registration Date: {timezone.localtime(organization.created_at).strftime('%Y-%m-%d %H:%M')}\\n"
                f"Status: Pending Approval\\n\\n"
                "Please review this registration request in the Second Life Admin Dashboard."
            )
            transaction.on_commit(lambda: send_platform_email(
                'givesthingsasecondlife@gmail.com',
                'New Organization Registration Request — Second Life',
                org_email
            ))

        NotificationService.send(
            user=user,
            title="Welcome to SecondLife! 🌱",
            message=(
                "Thank you for joining our circular community. "
                "Give things a second life, reduce waste, and create "
                "social impact."
            ),
            notif_type="REGISTRATION",
            link=(
                "/donor"
                if user.role == User.Role.DONOR
                else "/receiver"
            )
        )

        ActivityLog.objects.create(
            user=user,
            action="USER_REGISTERED",
            description=(
                f"New {user.account_type} {user.role} registered: "
                f"{user.name} ({user.email})."
            )
        )

        return user


# ============================================================
# CHANGE PASSWORD
# ============================================================

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        required=True
    )

    new_password = serializers.CharField(
        required=True,
        min_length=6
    )


# ============================================================
# PROFILE UPDATE
# ============================================================

class ProfileUpdateSerializer(serializers.ModelSerializer):
    bio = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100,
        error_messages={'max_length': 'Bio cannot exceed 100 characters.'}
    )

    preferred_categories = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )

    needed_categories = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )

    pickup_radius = serializers.IntegerField(
        required=False,
        min_value=1
    )

    latitude = serializers.DecimalField(
        required=False,
        allow_null=True,
        max_digits=9,
        decimal_places=6,
    )

    longitude = serializers.DecimalField(
        required=False,
        allow_null=True,
        max_digits=9,
        decimal_places=6,
    )

    handover_preference = serializers.CharField(
        required=False,
        allow_blank=True
    )

    class Meta:
        model = User
        fields = [
            'name',
            'phone',
            'address',
            'city',
            'country',
            'bio',
            'preferred_categories',
            'needed_categories',
            'pickup_radius',
            'latitude',
            'longitude',
            'handover_preference',
        ]

    def validate_name(self, value):
        value = ' '.join(str(value or '').split())
        if not value or len(value) < 2 or len(value) > 100:
            raise serializers.ValidationError('Enter a name between 2 and 100 characters.')
        if not re.fullmatch(r"[\\w\\u0300-\\u036f .'-]+", value, flags=re.UNICODE) or any(ch.isdigit() or ch == '_' for ch in value):
            raise serializers.ValidationError('Name may contain letters, spaces, apostrophes, hyphens, and periods only.')
        return value

    def validate_address(self, value):
        value = ' '.join(str(value or '').split())
        if len(value) < 4 or len(value) > 255 or not any(ch.isalnum() for ch in value):
            raise serializers.ValidationError('Enter a valid address between 4 and 255 characters.')
        return value

    def update(self, instance, validated_data):
        """
        Update both User and Profile data.

        The serializer operates on the User instance.
        Profile-specific fields are saved to the related Profile.
        """

        profile, created = Profile.objects.get_or_create(
            user=instance
        )

        # ----------------------------------------------------
        # PROFILE FIELDS
        # ----------------------------------------------------

        if 'bio' in validated_data:
            profile.bio = validated_data['bio']

        if 'preferred_categories' in validated_data:
            profile.preferred_categories = (
                validated_data['preferred_categories']
            )

        if 'needed_categories' in validated_data:
            profile.needed_categories = (
                validated_data['needed_categories']
            )

        if 'pickup_radius' in validated_data:
            profile.pickup_radius = (
                validated_data['pickup_radius']
            )

        if 'latitude' in validated_data:
            profile.latitude = validated_data['latitude']

        if 'longitude' in validated_data:
            profile.longitude = validated_data['longitude']

        if 'handover_preference' in validated_data:
            profile.handover_preference = (
                validated_data['handover_preference']
            )

        profile.save()

        # ----------------------------------------------------
        # USER FIELDS
        # ----------------------------------------------------

        user_fields = [
            'name',
            'phone',
            'address',
            'city',
            'country',
        ]

        changed_user_fields = []

        for field in user_fields:
            if field in validated_data:
                setattr(
                    instance,
                    field,
                    validated_data[field]
                )
                changed_user_fields.append(field)

        if changed_user_fields:
            instance.save(
                update_fields=changed_user_fields
            )

        return instance


# ============================================================
# VERIFY EMAIL OTP
# ============================================================

class VerifyEmailOTPSerializer(serializers.Serializer):

    email = serializers.EmailField()

    otp = serializers.CharField(
        min_length=6,
        max_length=6
    )

    def validate_otp(self, value):

        if not value.isdigit():
            raise serializers.ValidationError(
                'OTP must contain exactly 6 digits.'
            )

        return value