import uuid

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from rest_framework.exceptions import ValidationError, PermissionDenied

from donations.models import Donation
from item_requests.models import DonationRequest
from connections.models import Connection, Delivery
from dashboard.models import ActivityLog

from services.notification_service import NotificationService


# =============================================================
# EMAIL HELPER
# =============================================================

def send_connection_email(recipient_email, subject, message):
    from services.email_service import send_platform_email
    return send_platform_email(recipient_email, subject, message)


# =============================================================
# CONNECTION SERVICE
# =============================================================

class ConnectionService:

    # =========================================================
    # APPROVE REQUEST
    # =========================================================

    @staticmethod
    @transaction.atomic
    def approve_request(
        donation_request_id: int,
        donor_user,
        scheduled_date="",
        pickup_time_slot="",
        notes="",
    ):

        req = DonationRequest.objects.select_for_update().select_related(
            'donation',
            'donation__donor',
            'receiver',
        ).get(id=donation_request_id)

        donation = Donation.objects.select_for_update().get(
            id=req.donation_id
        )

        # -----------------------------------------------------
        # CHECK PERMISSION
        # -----------------------------------------------------

        if (
            donor_user.role != 'ADMIN'
            and donation.donor_id != donor_user.id
        ):
            raise PermissionDenied(
                "You do not have permission to approve requests "
                "for this donation."
            )

        # -----------------------------------------------------
        # CHECK REQUEST / DONATION STATUS
        # -----------------------------------------------------

        if req.status != DonationRequest.Status.PENDING:
            raise ValidationError(
                f"Request cannot be approved because "
                f"its status is {req.status}."
            )

        if donation.status != Donation.Status.AVAILABLE:
            raise ValidationError(
                "This donation is no longer available for matching."
            )

        # -----------------------------------------------------
        # UPDATE REQUEST
        # -----------------------------------------------------

        req.status = DonationRequest.Status.APPROVED

        req.save(
            update_fields=[
                'status',
                'updated_at',
            ]
        )

        # -----------------------------------------------------
        # UPDATE DONATION
        # -----------------------------------------------------

        donation.status = Donation.Status.MATCHED

        donation.save(
            update_fields=[
                'status',
                'updated_at',
            ]
        )

        # One donation can have only one successful match. Close any
        # other pending requests so the same item cannot be allocated twice.
        other_requests = DonationRequest.objects.filter(
            donation=donation,
            status=DonationRequest.Status.PENDING,
        ).exclude(pk=req.pk).select_related('receiver')

        for other_req in other_requests:
            other_req.status = DonationRequest.Status.REJECTED
            other_req.rejection_reason = (
                "This donation was matched with another receiver."
            )
            other_req.save(
                update_fields=[
                    'status',
                    'rejection_reason',
                    'updated_at',
                ]
            )

            NotificationService.send(
                user=other_req.receiver,
                title="Request Update",
                message=(
                    f"'{donation.title}' has been matched with another "
                    "receiver, so this request could not be fulfilled."
                ),
                notif_type="REQUEST_REJECTED",
                link="/receiver/requests",
            )

            send_connection_email(
                other_req.receiver.email,
                "Second Life - Donation Request Update",
                (
                    f"Hello {other_req.receiver.name},\n\n"
                    f"Your request for '{donation.title}' on Second Life "
                    "could not be fulfilled because the donation has been "
                    "matched with another receiver.\n\n"
                    "You can continue browsing Second Life for other "
                    "available items.\n\n"
                    "Regards,\n"
                    "Second Life Team\n\n"
                    "This is an automated email. Please do not reply directly "
                    "to this message.\n"
                ),
            )

        # -----------------------------------------------------
        # CREATE CONNECTION
        # -----------------------------------------------------

        connection = Connection.objects.create(
            donation=donation,
            donor=donation.donor,
            receiver=req.receiver,
            request=req,
            status=Connection.Status.ACCEPTED,
            scheduled_date=(
                scheduled_date
                or donation.pickup_date
                or "Tomorrow, 10:00 AM"
            ),
            pickup_time_slot=(
                pickup_time_slot
                or donation.pickup_time
                or "10:00 AM - 12:00 PM"
            ),
            pickup_address=donation.location,
            courier_notes=notes or "",
        )

        # -----------------------------------------------------
        # CREATE TRACKING NUMBER
        # -----------------------------------------------------

        tracking_num = (
            f"SL-{uuid.uuid4().hex[:8].upper()}"
        )

        # -----------------------------------------------------
        # INITIAL DELIVERY TIMELINE
        # -----------------------------------------------------

        now_str = timezone.now().strftime(
            "%b %d, %Y %I:%M %p"
        )

        initial_steps = [
            {
                "step": "Request Approved",
                "status": "COMPLETED",
                "timestamp": now_str,
            },
            {
                "step": "Connection Scheduled",
                "status": "COMPLETED",
                "timestamp": now_str,
            },
            {
                "step": "Processing & Prep",
                "status": "IN_PROGRESS",
                "timestamp": (
                    "Estimated "
                    + (scheduled_date or "Tomorrow")
                ),
            },
            {
                "step": "Handover & Delivery",
                "status": "PENDING",
                "timestamp": "Pending pickup",
            },
            {
                "step": "Impact Recorded",
                "status": "PENDING",
                "timestamp": "Pending completion",
            },
        ]

        # -----------------------------------------------------
        # CREATE DELIVERY
        # -----------------------------------------------------

        delivery = Delivery.objects.create(
            connection=connection,
            tracking_code=tracking_num,
            status=Delivery.DeliveryStatus.SCHEDULED,
            estimated_arrival=(
                f"{scheduled_date} "
                f"({pickup_time_slot})"
            ),
            timeline_steps=initial_steps,
        )

        # =====================================================
        # IN-APP NOTIFICATION TO RECEIVER
        # =====================================================

        NotificationService.send(
            user=req.receiver,
            title="Request Approved! 🎉",
            message=(
                f"Your request for '{donation.title}' "
                f"has been accepted by "
                f"{donation.donor.name}. "
                f"Scheduled for {scheduled_date}."
            ),
            notif_type="REQUEST_APPROVED",
            link=(
                f"/receiver/connections/{connection.id}"
            ),
        )

        # =====================================================
        # IN-APP NOTIFICATION TO DONOR
        # =====================================================

        NotificationService.send(
            user=donation.donor,
            title="Match Confirmed",
            message=(
                f"You agreed to hand over "
                f"'{donation.title}' to "
                f"{req.receiver.name}. "
                f"Pickup scheduled for {scheduled_date}."
            ),
            notif_type="CONNECTION_CREATED",
            link=(
                f"/donor/connections/{connection.id}"
            ),
        )

        # =====================================================
        # EMAIL TO RECEIVER
        # =====================================================

        receiver_email = getattr(
            req.receiver,
            'email',
            '',
        )

        receiver_subject = (
            "Second Life - Donation Request Approved"
        )

        receiver_message = f"""
Hello {req.receiver.name},

We are pleased to inform you that your donation request has been approved on Second Life.

Your request has been accepted by {donation.donor.name}.

Donation Details
----------------
Item: {donation.title}
Category: {donation.category.name if donation.category else 'N/A'}
Condition: {donation.get_condition_display()}
Quantity: {donation.quantity}
Delivery Option: {donation.get_delivery_option_display()}
Location: {donation.location}
City: {donation.city}

Connection Details
------------------
Donor: {donation.donor.name}
Donor Email: {donation.donor.email}
Scheduled Date: {scheduled_date}
Pickup / Delivery Time: {pickup_time_slot}
Tracking Code: {tracking_num}

Notes:
{notes or 'No additional notes provided.'}

Your donation request is now approved and the connection has been established.

Please log in to your Second Life account to view the connection and follow the delivery progress.

Regards,
Second Life Team

This is an automated email. Please do not reply directly to this message.
"""

        send_connection_email(
            recipient_email=receiver_email,
            subject=receiver_subject,
            message=receiver_message,
        )

        # =====================================================
        # EMAIL TO DONOR
        # =====================================================

        donor_email = getattr(
            donation.donor,
            'email',
            '',
        )

        donor_subject = (
            "Second Life - Donation Match Confirmed"
        )

        donor_message = f"""
Hello {donation.donor.name},

Your donation has been successfully matched with a receiver on Second Life.

Donation Details
----------------
Item: {donation.title}
Category: {donation.category.name if donation.category else 'N/A'}
Condition: {donation.get_condition_display()}
Quantity: {donation.quantity}
Delivery Option: {donation.get_delivery_option_display()}
Location: {donation.location}
City: {donation.city}

Receiver Details
----------------
Receiver: {req.receiver.name}
Receiver Email: {req.receiver.email}

Connection Details
------------------
Scheduled Date: {scheduled_date}
Pickup / Delivery Time: {pickup_time_slot}
Tracking Code: {tracking_num}

Notes:
{notes or 'No additional notes provided.'}

The receiver has been notified that the request was approved.

Please log in to your Second Life account to manage the connection and follow the delivery process.

Thank you for helping give items a second life.

Regards,
Second Life Team

This is an automated email. Please do not reply directly to this message.
"""

        send_connection_email(
            recipient_email=donor_email,
            subject=donor_subject,
            message=donor_message,
        )

        # =====================================================
        # ACTIVITY LOG
        # =====================================================

        ActivityLog.objects.create(
            user=donor_user,
            action="REQUEST_APPROVED",
            description=(
                f"{donor_user.name} approved request "
                f"#{req.id} for donation "
                f"'{donation.title}'. "
                f"Connection #{connection.id} established."
            ),
        )

        return connection

    # =========================================================
    # REJECT REQUEST
    # =========================================================

    @staticmethod
    @transaction.atomic
    def reject_request(
        donation_request_id: int,
        donor_user,
        reason="",
    ):

        req = DonationRequest.objects.select_for_update().select_related(
            'donation',
            'donation__donor',
            'receiver',
        ).get(id=donation_request_id)

        donation = req.donation

        # -----------------------------------------------------
        # CHECK PERMISSION
        # -----------------------------------------------------

        if (
            donor_user.role != 'ADMIN'
            and donation.donor_id != donor_user.id
        ):
            raise PermissionDenied(
                "You do not have permission to reject "
                "this request."
            )

        # -----------------------------------------------------
        # CHECK STATUS
        # -----------------------------------------------------

        if req.status != DonationRequest.Status.PENDING:
            raise ValidationError(
                f"Request cannot be rejected because "
                f"its status is {req.status}."
            )

        # -----------------------------------------------------
        # REJECTION REASON
        # -----------------------------------------------------

        rejection_reason = (
            reason
            or "Item is no longer available or was "
               "matched with another recipient."
        )

        # -----------------------------------------------------
        # UPDATE REQUEST
        # -----------------------------------------------------

        req.status = DonationRequest.Status.REJECTED
        req.rejection_reason = rejection_reason

        req.save(
            update_fields=[
                'status',
                'rejection_reason',
                'updated_at',
            ]
        )

        # =====================================================
        # IN-APP NOTIFICATION TO RECEIVER
        # =====================================================

        NotificationService.send(
            user=req.receiver,
            title="Request Update",
            message=(
                f"Your request for '{donation.title}' "
                f"could not be fulfilled at this time: "
                f"{rejection_reason}"
            ),
            notif_type="REQUEST_REJECTED",
            link="/receiver/requests",
        )

        # =====================================================
        # EMAIL TO RECEIVER
        # =====================================================

        receiver_email = getattr(
            req.receiver,
            'email',
            '',
        )

        receiver_subject = (
            "Second Life - Donation Request Update"
        )

        receiver_message = f"""
Hello {req.receiver.name},

We are writing to inform you that your donation request on Second Life was not approved at this time.

Request Details
---------------
Item: {donation.title}
Category: {donation.category.name if donation.category else 'N/A'}
Condition: {donation.get_condition_display()}
Quantity: {donation.quantity}
Location: {donation.location}
City: {donation.city}

Request Status:
Rejected

Reason:
{rejection_reason}

We understand that this may be disappointing. You can continue browsing Second Life for other available items that may meet your needs.

Thank you for using Second Life.

Regards,
Second Life Team

This is an automated email. Please do not reply directly to this message.
"""

        send_connection_email(
            recipient_email=receiver_email,
            subject=receiver_subject,
            message=receiver_message,
        )

        # =====================================================
        # ACTIVITY LOG
        # =====================================================

        ActivityLog.objects.create(
            user=donor_user,
            action="REQUEST_REJECTED",
            description=(
                f"{donor_user.name} declined request "
                f"#{req.id} for donation "
                f"'{donation.title}'."
            ),
        )

        return req

    # =========================================================
    # UPDATE DELIVERY STATUS
    # =========================================================

    @staticmethod
    @transaction.atomic
    def update_delivery_status(
        connection_id: int,
        new_status: str,
        admin_or_courier_user=None,
    ):

        connection = (
            Connection.objects
            .select_for_update()
            .select_related(
                'donation',
                'donor',
                'receiver',
            )
            .get(id=connection_id)
        )

        delivery = connection.delivery

        # -----------------------------------------------------
        # NORMALIZE STATUS
        # -----------------------------------------------------

        new_status = str(
            new_status
        ).upper().strip()

        # -----------------------------------------------------
        # VALID STATUS TRANSITIONS
        # -----------------------------------------------------

        valid_transitions = {
            'SCHEDULED': [
                'PROCESSING',
                'TRANSIT',
                'CANCELLED',
            ],
            'PROCESSING': [
                'TRANSIT',
                'ARRIVING',
            ],
            'TRANSIT': [
                'ARRIVING',
                'DELIVERED',
            ],
            'ARRIVING': [
                'DELIVERED',
            ],
            'DELIVERED': [
                'COMPLETED',
            ],
        }

        current_status = delivery.status

        if new_status not in valid_transitions.get(
            current_status,
            [],
        ):

            raise ValidationError(
                f"Delivery cannot move from "
                f"{current_status} to {new_status}."
            )

        # -----------------------------------------------------
        # UPDATE DELIVERY STATUS
        # -----------------------------------------------------

        delivery.status = new_status

        now_str = timezone.now().strftime(
            "%b %d, %Y %I:%M %p"
        )

        # -----------------------------------------------------
        # UPDATE TIMELINE
        # -----------------------------------------------------

        steps = delivery.timeline_steps or []

        for step in steps:

            step_name = str(
                step.get('step', '')
            ).upper()

            if (
                new_status in step_name
                or (
                    new_status == 'PROCESSING'
                    and 'PROCESSING' in step_name
                )
                or (
                    new_status == 'TRANSIT'
                    and 'DELIVERY' in step_name
                )
                or (
                    new_status == 'ARRIVING'
                    and 'DELIVERY' in step_name
                )
                or (
                    new_status == 'DELIVERED'
                    and 'DELIVERY' in step_name
                )
            ):
                step['status'] = 'COMPLETED'
                step['timestamp'] = now_str

        # -----------------------------------------------------
        # SAVE DELIVERY
        # -----------------------------------------------------

        delivery.timeline_steps = steps

        delivery.save()

        # =====================================================
        # DELIVERY STATUS EMAIL
        # =====================================================

        donation = connection.donation

        receiver_email = getattr(
            connection.receiver,
            'email',
            '',
        )

        donor_email = getattr(
            connection.donor,
            'email',
            '',
        )

        # -----------------------------------------------------
        # FRIENDLY STATUS TEXT
        # -----------------------------------------------------

        status_display = {
            'SCHEDULED': 'Scheduled',
            'PROCESSING': 'Processing',
            'TRANSIT': 'In Transit',
            'ARRIVING': 'Arriving Soon',
            'DELIVERED': 'Delivered',
            'COMPLETED': 'Completed',
            'CANCELLED': 'Cancelled',
        }.get(
            new_status,
            new_status.replace('_', ' ').title(),
        )

        # =====================================================
        # SPECIAL DELIVERED HANDLING
        # =====================================================

        if new_status == 'DELIVERED':

            connection.status = (
                Connection.Status.DELIVERED
            )

            donation.status = (
                Donation.Status.DELIVERED
            )

            donation.save(
                update_fields=[
                    'status',
                    'updated_at',
                ]
            )

            connection.save(
                update_fields=[
                    'status',
                    'updated_at',
                ]
            )

            # -------------------------------------------------
            # IN-APP RECEIVER NOTIFICATION
            # -------------------------------------------------

            NotificationService.send(
                user=connection.receiver,
                title="Item Delivered! 📦",
                message=(
                    f"'{donation.title}' has been "
                    f"successfully delivered/received."
                ),
                notif_type="DELIVERY_UPDATE",
                link=(
                    f"/receiver/connections/"
                    f"{connection.id}"
                ),
            )

            # -------------------------------------------------
            # IN-APP DONOR NOTIFICATION
            # -------------------------------------------------

            NotificationService.send(
                user=connection.donor,
                title="Handover Complete!",
                message=(
                    f"'{donation.title}' was successfully "
                    f"delivered to "
                    f"{connection.receiver.name}."
                ),
                notif_type="DONATION_DELIVERED",
                link=(
                    f"/donor/connections/"
                    f"{connection.id}"
                ),
            )

            # -------------------------------------------------
            # EMAIL RECEIVER - DELIVERED
            # -------------------------------------------------

            receiver_subject = (
                "Second Life - Donation Delivered Successfully"
            )

            receiver_message = f"""
Hello {connection.receiver.name},

Your requested donation has been successfully delivered through Second Life.

Donation Details
----------------
Item: {donation.title}
Category: {donation.category.name if donation.category else 'N/A'}
Condition: {donation.get_condition_display()}
Quantity: {donation.quantity}
Location: {donation.location}
City: {donation.city}

Delivery Details
----------------
Tracking Code: {delivery.tracking_code}
Delivery Status: Delivered
Delivered At: {now_str}

The item has been successfully delivered/received.

Thank you for being part of the Second Life community and helping us give useful items a second life.

Regards,
Second Life Team

This is an automated email. Please do not reply directly to this message.
"""

            send_connection_email(
                recipient_email=receiver_email,
                subject=receiver_subject,
                message=receiver_message,
            )

            # -------------------------------------------------
            # EMAIL DONOR - DELIVERED
            # -------------------------------------------------

            donor_subject = (
                "Second Life - Donation Delivered Successfully"
            )

            donor_message = f"""
Hello {connection.donor.name},

Your donated item has been successfully delivered to the receiver through Second Life.

Donation Details
----------------
Item: {donation.title}
Category: {donation.category.name if donation.category else 'N/A'}
Condition: {donation.get_condition_display()}
Quantity: {donation.quantity}
Location: {donation.location}
City: {donation.city}

Receiver Details
----------------
Receiver: {connection.receiver.name}
Receiver Email: {connection.receiver.email}

Delivery Details
----------------
Tracking Code: {delivery.tracking_code}
Delivery Status: Delivered
Delivered At: {now_str}

Your donation has successfully reached its intended receiver.

Thank you for helping give this item a second life.

Regards,
Second Life Team

This is an automated email. Please do not reply directly to this message.
"""

            send_connection_email(
                recipient_email=donor_email,
                subject=donor_subject,
                message=donor_message,
            )

        else:

            # =================================================
            # IN-APP DELIVERY UPDATE - RECEIVER
            # =================================================

            NotificationService.send(
                user=connection.receiver,
                title=f"Delivery Update: {status_display}",
                message=(
                    f"The delivery status of "
                    f"'{donation.title}' is now "
                    f"{status_display}."
                ),
                notif_type="DELIVERY_UPDATE",
                link=(
                    f"/receiver/connections/"
                    f"{connection.id}"
                ),
            )

            # =================================================
            # IN-APP DELIVERY UPDATE - DONOR
            # =================================================

            NotificationService.send(
                user=connection.donor,
                title=f"Delivery Update: {status_display}",
                message=(
                    f"The delivery status of "
                    f"'{donation.title}' is now "
                    f"{status_display}."
                ),
                notif_type="DELIVERY_UPDATE",
                link=(
                    f"/donor/connections/"
                    f"{connection.id}"
                ),
            )

            # =================================================
            # EMAIL RECEIVER - DELIVERY UPDATE
            # =================================================

            receiver_subject = (
                f"Second Life - Delivery Update: "
                f"{status_display}"
            )

            receiver_message = f"""
Hello {connection.receiver.name},

There has been an update to the delivery status of your requested donation on Second Life.

Donation Details
----------------
Item: {donation.title}
Category: {donation.category.name if donation.category else 'N/A'}
Condition: {donation.get_condition_display()}
Quantity: {donation.quantity}
Location: {donation.location}
City: {donation.city}

Delivery Details
----------------
Tracking Code: {delivery.tracking_code}
Current Status: {status_display}
Updated At: {now_str}

Please log in to your Second Life account to view the latest delivery progress.

Regards,
Second Life Team

This is an automated email. Please do not reply directly to this message.
"""

            send_connection_email(
                recipient_email=receiver_email,
                subject=receiver_subject,
                message=receiver_message,
            )

            # =================================================
            # EMAIL DONOR - DELIVERY UPDATE
            # =================================================

            donor_subject = (
                f"Second Life - Delivery Update: "
                f"{status_display}"
            )

            donor_message = f"""
Hello {connection.donor.name},

There has been an update to the delivery status of your donated item on Second Life.

Donation Details
----------------
Item: {donation.title}
Category: {donation.category.name if donation.category else 'N/A'}
Condition: {donation.get_condition_display()}
Quantity: {donation.quantity}
Location: {donation.location}
City: {donation.city}

Receiver Details
----------------
Receiver: {connection.receiver.name}
Receiver Email: {connection.receiver.email}

Delivery Details
----------------
Tracking Code: {delivery.tracking_code}
Current Status: {status_display}
Updated At: {now_str}

Please log in to your Second Life account to view the latest delivery progress.

Regards,
Second Life Team

This is an automated email. Please do not reply directly to this message.
"""

            send_connection_email(
                recipient_email=donor_email,
                subject=donor_subject,
                message=donor_message,
            )

        # =====================================================
        # ACTIVITY LOG
        # =====================================================

        ActivityLog.objects.create(
            user=(
                admin_or_courier_user
                or connection.donor
            ),
            action="DELIVERY_STATUS_UPDATED",
            description=(
                f"Delivery for donation "
                f"'{donation.title}' "
                f"(Connection #{connection.id}) "
                f"updated to {new_status}."
            ),
        )

        return connection