from rest_framework import serializers

from item_requests.models import DonationRequest
from donations.models import Donation
from donations.serializers import DonationListSerializer
from accounts.serializers import UserSerializer

from notifications.models import Notification
from services.notification_service import NotificationService
from dashboard.models import ActivityLog


def send_notification_email(recipient_email, subject, message):
    from services.email_service import send_platform_email
    return send_platform_email(recipient_email, subject, message)


class DonationRequestSerializer(serializers.ModelSerializer):

    donation = DonationListSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)
    connection_id = serializers.SerializerMethodField()

    class Meta:
        model = DonationRequest

        fields = [
            'id',
            'donation',
            'receiver',
            'message',
            'status',
            'rejection_reason',
            'connection_id',
            'created_at',
            'updated_at',
        ]

        read_only_fields = [
            'id',
            'status',
            'rejection_reason',
            'created_at',
            'updated_at',
        ]

    def get_connection_id(self, obj):

        if hasattr(obj, 'connection'):
            return obj.connection.id

        return None


class DonationRequestCreateSerializer(serializers.ModelSerializer):

    donation_id = serializers.IntegerField(required=True)

    class Meta:
        model = DonationRequest

        fields = [
            'id',
            'donation_id',
            'message',
        ]

        read_only_fields = [
            'id',
        ]

    def validate(self, attrs):

        user = self.context['request'].user
        donation_id = attrs.get('donation_id')

        # ---------------------------------------------------------
        # 1. CHECK DONATION EXISTS
        # ---------------------------------------------------------

        try:
            donation = Donation.objects.select_related(
                'donor',
                'category',
            ).get(id=donation_id)

        except Donation.DoesNotExist:

            raise serializers.ValidationError({
                "donation_id": "Specified donation does not exist."
            })

        # ---------------------------------------------------------
        # 2. USER CANNOT REQUEST OWN DONATION
        # ---------------------------------------------------------

        if donation.donor_id == user.id:

            raise serializers.ValidationError({
                "donation_id": "You cannot request your own donation."
            })

        # ---------------------------------------------------------
        # 3. DONATION MUST BE AVAILABLE
        # ---------------------------------------------------------

        if donation.status != Donation.Status.AVAILABLE:

            raise serializers.ValidationError({
                "donation_id": (
                    f"This item is no longer available "
                    f"(Status: {donation.status})."
                )
            })

        # ---------------------------------------------------------
        # 4. PREVENT DUPLICATE ACTIVE REQUESTS
        # ---------------------------------------------------------

        if DonationRequest.objects.filter(
            donation=donation,
            receiver=user,
            status__in=[
                DonationRequest.Status.PENDING,
                DonationRequest.Status.APPROVED,
            ],
        ).exists():

            raise serializers.ValidationError({
                "donation_id": (
                    "You already have an active request "
                    "for this item."
                )
            })

        # ---------------------------------------------------------
        # 5. STORE DONATION OBJECT TEMPORARILY
        # ---------------------------------------------------------

        attrs['donation_obj'] = donation

        return attrs

    def create(self, validated_data):

        user = self.context['request'].user

        # ---------------------------------------------------------
        # 1. GET DONATION
        # ---------------------------------------------------------

        donation = validated_data.pop('donation_obj')

        validated_data.pop('donation_id')

        # ---------------------------------------------------------
        # 2. CREATE DONATION REQUEST
        # ---------------------------------------------------------

        req = DonationRequest.objects.create(
            donation=donation,
            receiver=user,
            **validated_data,
        )

        # =========================================================
        # 3. IN-APP NOTIFICATION TO DONOR
        # =========================================================

        NotificationService.send(
            user=donation.donor,
            title="New Item Request! 📬",
            message=(
                f"{user.name} submitted a request for "
                f"your donation '{donation.title}'."
            ),
            notif_type=Notification.NotificationType.REQUEST_RECEIVED,
            link="/donor/requests",
        )

        # =========================================================
        # 4. EMAIL TO DONOR
        # =========================================================

        donor_email = getattr(
            donation.donor,
            'email',
            '',
        )

        donor_subject = (
            "Second Life - New Donation Request Received"
        )

        donor_message = f"""
Hello {donation.donor.name},

You have received a new donation request on Second Life.

Donation Details
----------------
Item: {donation.title}
Category: {donation.category.name if donation.category else 'N/A'}
Condition: {donation.get_condition_display()}
Quantity: {donation.quantity}
Delivery Option: {donation.get_delivery_option_display()}
Location: {donation.location}
City: {donation.city}

Description:
{donation.description}

Request Details
---------------
Requested By: {user.name}
Receiver Location: {user.city or 'Not provided'}
Receiver Address: {user.address or 'Not provided'}
Receiver Contact: {user.phone or 'Not provided'}
Receiver Email: {user.email}

Message from Receiver:
{req.message}

Request Status:
Pending Review

The receiver is interested in receiving your donated item.

Please log in to your Second Life account to review and manage this request.

Regards,
Second Life Team

This is an automated email. Please do not reply directly to this message.
"""

        send_notification_email(
            recipient_email=donor_email,
            subject=donor_subject,
            message=donor_message,
        )

        # =========================================================
        # 5. EMAIL CONFIRMATION TO RECEIVER
        # =========================================================

        receiver_email = getattr(
            user,
            'email',
            '',
        )

        receiver_subject = (
            "Second Life - Donation Request Submitted Successfully"
        )

        receiver_message = f"""
Hello {user.name},

Your donation request has been successfully submitted on Second Life.

Request Details
---------------
Item: {donation.title}
Category: {donation.category.name if donation.category else 'N/A'}
Condition: {donation.get_condition_display()}
Quantity: {donation.quantity}
Delivery Option: {donation.get_delivery_option_display()}
Location: {donation.location}
City: {donation.city}

Description:
{donation.description}

Your Message:
{req.message}

Request Status:
Pending Review

The donor has been notified of your request.

You will receive another notification when the donor takes action on your request.

Thank you for using Second Life and helping make a positive impact through reuse and community sharing.

Regards,
Second Life Team

This is an automated email. Please do not reply directly to this message.
"""

        send_notification_email(
            recipient_email=receiver_email,
            subject=receiver_subject,
            message=receiver_message,
        )

        # =========================================================
        # 6. ACTIVITY LOG
        # =========================================================

        ActivityLog.objects.create(
            user=user,
            action="REQUEST_SUBMITTED",
            description=(
                f"Receiver {user.name} requested item "
                f"'{donation.title}' from donor "
                f"{donation.donor.name}."
            ),
        )

        # ---------------------------------------------------------
        # RETURN CREATED REQUEST
        # ---------------------------------------------------------

        return req