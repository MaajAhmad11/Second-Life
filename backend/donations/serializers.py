from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import serializers

from donations.models import Category, Donation, DonationImage, SavedItem
from accounts.serializers import UserSerializer


User = get_user_model()


def resolve_public_image_url(url, request=None):
    """Return frontend-hosted URLs for static /images assets and backend media URLs otherwise."""
    if not url:
        return None

    url = str(url)

    if url.startswith('/images/'):
        origin = None
        if request is not None:
            origin = request.headers.get('Origin')

        origin = origin or getattr(settings, 'FRONTEND_URL', '')
        origin = str(origin).rstrip('/')

        if origin:
            return f'{origin}{url}'

    if request and url.startswith('/'):
        return request.build_absolute_uri(url)

    return url


# =============================================================
# EMAIL HELPER
# =============================================================

def send_donation_email(recipient_email, subject, message):
    from services.email_service import send_platform_email
    return send_platform_email(recipient_email, subject, message)


# =============================================================
# CATEGORY SERIALIZER
# =============================================================

class CategorySerializer(serializers.ModelSerializer):

    donations_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'slug',
            'icon',
            'description',
            'donations_count',
        ]

    def get_donations_count(self, obj):
        return obj.donations.filter(
            status='AVAILABLE'
        ).count()


# =============================================================
# DONATION IMAGE SERIALIZER
# =============================================================

class DonationImageSerializer(serializers.ModelSerializer):

    url = serializers.SerializerMethodField()

    class Meta:
        model = DonationImage
        fields = [
            'id',
            'image',
            'image_url',
            'is_primary',
            'url',
        ]

    def get_url(self, obj):
        request = self.context.get('request')

        if obj.image:
            url = obj.image.url
        elif obj.image_url:
            url = obj.image_url
        else:
            return None

        url = resolve_public_image_url(url, request)
        if obj.created_at:
            separator = '&' if '?' in url else '?'
            url = f'{url}{separator}v={obj.created_at.timestamp()}'
        return url


# =============================================================
# DONATION LIST SERIALIZER
# =============================================================

class DonationListSerializer(serializers.ModelSerializer):

    weight_kg = serializers.ReadOnlyField()
    total_weight_kg = serializers.ReadOnlyField()
    category = CategorySerializer(read_only=True)

    donor_name = serializers.CharField(
        source='donor.name',
        read_only=True,
    )

    donor_initials = serializers.CharField(
        source='donor.initials',
        read_only=True,
    )

    donor_account_type = serializers.CharField(
        source='donor.account_type',
        read_only=True,
    )

    donor_is_verified = serializers.BooleanField(
        source='donor.is_verified',
        read_only=True,
    )

    primary_image = serializers.SerializerMethodField()
    requests_count = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    match_score = serializers.SerializerMethodField()
    distance_miles = serializers.SerializerMethodField()

    class Meta:
        model = Donation

        fields = [
            'id',
            'title',
            'description',
            'category',
            'condition',
            'quantity',
            'delivery_option',
            'location',
            'city',
            'status',
            'dimensions',
            'weight',
            'weight_kg',
            'total_weight_kg',
            'pickup_date',
            'pickup_time',
            'pickup_latitude',
            'pickup_longitude',
            'views_count',
            'donor_name',
            'donor_initials',
            'donor_account_type',
            'donor_is_verified',
            'primary_image',
            'requests_count',
            'is_saved',
            'match_score',
            'distance_miles',
            'created_at',
        ]

    def get_primary_image(self, obj):
        request = self.context.get('request')
        primary = obj.images.filter(is_primary=True).first() or obj.images.first()

        if not primary:
            return None

        if primary.image:
            url = primary.image.url
        elif primary.image_url:
            url = primary.image_url
        else:
            return None

        url = resolve_public_image_url(url, request)
        if primary.created_at:
            separator = '&' if '?' in url else '?'
            url = f'{url}{separator}v={primary.created_at.timestamp()}'
        return url

    def get_requests_count(self, obj):
        return obj.requests.filter(
            status__in=['PENDING', 'APPROVED', 'MATCHED']
        ).count()

    def get_is_saved(self, obj):

        request = self.context.get('request')

        if request and request.user.is_authenticated:
            return obj.saved_by_users.filter(
                user=request.user
            ).exists()

        return False

    def get_distance_miles(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        profile = getattr(user, 'profile', None) if user and user.is_authenticated else None
        if not profile or profile.latitude is None or profile.longitude is None:
            return None
        if obj.pickup_latitude is None or obj.pickup_longitude is None:
            return None

        from math import radians, sin, cos, sqrt, atan2
        lat1, lon1 = radians(float(profile.latitude)), radians(float(profile.longitude))
        lat2, lon2 = radians(float(obj.pickup_latitude)), radians(float(obj.pickup_longitude))
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        miles = 3958.7613 * (2 * atan2(sqrt(a), sqrt(1 - a)))
        return round(miles, 1)


    def get_match_score(self, obj):

        request = self.context.get('request')

        if (
            request
            and request.user.is_authenticated
            and request.user.role == 'RECEIVER'
        ):
            from services.matching_service import MatchingService

            result = MatchingService.calculate_match_score(
                obj,
                request.user,
            )

            return result['score']

        return None


# =============================================================
# DONATION DETAIL SERIALIZER
# =============================================================

class DonationDetailSerializer(serializers.ModelSerializer):

    weight_kg = serializers.ReadOnlyField()
    total_weight_kg = serializers.ReadOnlyField()
    category = CategorySerializer(read_only=True)

    images = DonationImageSerializer(
        many=True,
        read_only=True,
    )

    donor = UserSerializer(read_only=True)

    donor_items_count = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    match_details = serializers.SerializerMethodField()
    distance_miles = serializers.SerializerMethodField()

    class Meta:
        model = Donation

        fields = [
            'id',
            'title',
            'description',
            'category',
            'condition',
            'quantity',
            'delivery_option',
            'location',
            'city',
            'status',
            'dimensions',
            'weight',
            'weight_kg',
            'total_weight_kg',
            'pickup_date',
            'pickup_time',
            'pickup_latitude',
            'pickup_longitude',
            'views_count',
            'images',
            'donor',
            'donor_items_count',
            'is_saved',
            'match_details',
            'distance_miles',
            'created_at',
            'updated_at',
        ]

    def get_donor_items_count(self, obj):

        return obj.donor.donations.filter(
            status__in=[
                'DELIVERED',
                'COMPLETED',
            ]
        ).count()

    def get_is_saved(self, obj):

        request = self.context.get('request')

        if request and request.user.is_authenticated:
            return obj.saved_by_users.filter(
                user=request.user
            ).exists()

        return False

    def get_distance_miles(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        profile = getattr(user, 'profile', None) if user and user.is_authenticated else None
        if not profile or profile.latitude is None or profile.longitude is None:
            return None
        if obj.pickup_latitude is None or obj.pickup_longitude is None:
            return None
        from math import radians, sin, cos, sqrt, atan2
        lat1, lon1 = radians(float(profile.latitude)), radians(float(profile.longitude))
        lat2, lon2 = radians(float(obj.pickup_latitude)), radians(float(obj.pickup_longitude))
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        return round(3958.7613 * (2 * atan2(sqrt(a), sqrt(1 - a))), 1)

    def get_match_details(self, obj):

        request = self.context.get('request')

        if (
            request
            and request.user.is_authenticated
            and request.user.role == 'RECEIVER'
        ):
            from services.matching_service import MatchingService

            return MatchingService.calculate_match_score(
                obj,
                request.user,
            )

        return None


# =============================================================
# DONATION CREATE SERIALIZER
# =============================================================

class DonationCreateSerializer(serializers.ModelSerializer):

    category_id = serializers.IntegerField(
        required=True
    )

    image_urls = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
    )

    class Meta:
        model = Donation

        fields = [
            'id',
            'category_id',
            'title',
            'description',
            'condition',
            'quantity',
            'delivery_option',
            'location',
            'city',
            'dimensions',
            'weight',
            'pickup_date',
            'pickup_time',
            'pickup_latitude',
            'pickup_longitude',
            'image_urls',
        ]

    def create(self, validated_data):

        # =====================================================
        # GET DATA
        # =====================================================

        category_id = validated_data.pop(
            'category_id'
        )

        image_urls = validated_data.pop(
            'image_urls',
            [],
        )

        category = Category.objects.get(
            id=category_id
        )

        donor = self.context['request'].user

        # =====================================================
        # CREATE DONATION
        # =====================================================

        donation = Donation.objects.create(
            donor=donor,
            category=category,
            status=Donation.Status.AVAILABLE,
            **validated_data
        )

        # =====================================================
        # HANDLE IMAGES
        # =====================================================

        if image_urls:

            for idx, img_url in enumerate(image_urls):

                DonationImage.objects.create(
                    donation=donation,
                    image_url=img_url,
                    is_primary=(idx == 0),
                )

        # No synthetic/default image is created.


        # =====================================================
        # ACTIVITY LOG
        # =====================================================

        from dashboard.models import ActivityLog

        ActivityLog.objects.create(
            user=donor,
            action="DONATION_CREATED",
            description=(
                f"Donor {donor.name} published "
                f"donation #{donation.id}: "
                f"'{donation.title}'."
            ),
        )

        # =====================================================
        # IN-APP NOTIFICATION TO DONOR
        # =====================================================

        from services.notification_service import NotificationService

        NotificationService.send(
            user=donor,
            title="Donation Published! 🌿",
            message=(
                f"Your donation '{donation.title}' "
                f"is now live and waiting to be matched "
                f"with someone in need."
            ),
            notif_type="DONATION_CREATED",
            link=f"/donor/donations/{donation.id}",
        )

        # =====================================================
        # EMAIL TO DONOR
        # =====================================================

        donor_email = getattr(
            donor,
            'email',
            '',
        )

        donor_subject = (
            "Second Life - Donation Published Successfully"
        )

        donor_message = f"""
Hello {donor.name},

Your donation has been successfully published on Second Life.

Donation Details
----------------
Item: {donation.title}
Category: {category.name if category else 'N/A'}
Condition: {donation.get_condition_display()}
Quantity: {donation.quantity}
Delivery Option: {donation.get_delivery_option_display()}
Location: {donation.location}
City: {donation.city}

Description:
{donation.description}

Status:
Available

Your donated item is now visible to registered receivers on Second Life.

Thank you for helping give useful items a second life and supporting community sharing.

Regards,
Second Life Team

This is an automated email. Please do not reply directly to this message.
"""

        send_donation_email(
            recipient_email=donor_email,
            subject=donor_subject,
            message=donor_message,
        )

        # =====================================================
        # FIND ALL RECEIVERS
        # =====================================================

        receivers = User.objects.filter(
            role='RECEIVER',
        ).exclude(
            email=''
        )

        # =====================================================
        # EMAIL + IN-APP NOTIFICATION TO ALL RECEIVERS
        # =====================================================

        for receiver in receivers:

            # -------------------------------------------------
            # IN-APP NOTIFICATION
            # -------------------------------------------------

            NotificationService.send(
                user=receiver,
                title="New Donation Available! 🎁",
                message=(
                    f"A new item '{donation.title}' "
                    f"has been added to Second Life "
                    f"and may be available for you."
                ),
                notif_type="DONATION_CREATED",
                link=f"/receiver/donations/{donation.id}",
            )

            # -------------------------------------------------
            # EMAIL
            # -------------------------------------------------

            receiver_email = getattr(
                receiver,
                'email',
                '',
            )

            receiver_subject = (
                "Second Life - New Donation Available"
            )

            receiver_message = f"""
Hello {receiver.name},

A new donation has been published on Second Life that may be useful to you.

Donation Details
----------------
Item: {donation.title}
Category: {category.name if category else 'N/A'}
Condition: {donation.get_condition_display()}
Quantity: {donation.quantity}
Delivery Option: {donation.get_delivery_option_display()}
Location: {donation.location}
City: {donation.city}

Description:
{donation.description}

Donor:
{donor.name}

The item is currently available for request.

Please log in to your Second Life account to view the donation and submit a request if it meets your needs.

Thank you for being part of the Second Life community.

Regards,
Second Life Team

This is an automated email. Please do not reply directly to this message.
"""

            send_donation_email(
                recipient_email=receiver_email,
                subject=receiver_subject,
                message=receiver_message,
            )

        # =====================================================
        # RETURN DONATION
        # =====================================================

        return donation


# =============================================================
# SAVED ITEM SERIALIZER
# =============================================================

class SavedItemSerializer(serializers.ModelSerializer):

    donation = DonationListSerializer(
        read_only=True
    )

    class Meta:
        model = SavedItem

        fields = [
            'id',
            'donation',
            'created_at',
        ]