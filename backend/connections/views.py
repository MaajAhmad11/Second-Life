from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from django.db import transaction

from connections.models import Connection, Delivery
from connections.serializers import ConnectionSerializer, DeliverySerializer
from accounts.permissions import IsAdmin
from donations.models import Donation
from item_requests.models import DonationRequest
from services.notification_service import NotificationService
from dashboard.models import ActivityLog
from services.email_service import send_platform_email

class ConnectionListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        queryset = Connection.objects.all().select_related(
            'donation', 'donation__category', 'donation__donor', 'donor', 'receiver', 'delivery'
        ).prefetch_related('donation__images')

        if user.role == 'DONOR':
            queryset = queryset.filter(donor=user)
        elif user.role == 'RECEIVER':
            queryset = queryset.filter(receiver=user)

        filter_type = request.query_params.get('filter', 'ALL').upper()
        if filter_type == 'UPCOMING':
            queryset = queryset.exclude(status__in=['COMPLETED', 'CANCELLED'])
        elif filter_type == 'COMPLETED':
            queryset = queryset.filter(status='COMPLETED')

        serializer = ConnectionSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

class ConnectionDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            connection = Connection.objects.select_related(
                'donation', 'donation__category', 'donation__donor', 'donor', 'receiver', 'delivery'
            ).prefetch_related('donation__images').get(pk=pk)
        except Connection.DoesNotExist:
            return Response({'error': 'Connection not found.'}, status=status.HTTP_404_NOT_FOUND)

        if request.user.role != 'ADMIN' and connection.donor_id != request.user.id and connection.receiver_id != request.user.id:
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        return Response(ConnectionSerializer(connection, context={'request': request}).data)

    def patch(self, request, pk):
        try:
            connection = Connection.objects.get(pk=pk)
        except Connection.DoesNotExist:
            return Response({'error': 'Connection not found.'}, status=status.HTTP_404_NOT_FOUND)

        if request.user.role != 'ADMIN' and connection.donor_id != request.user.id and connection.receiver_id != request.user.id:
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        # Allow updating scheduled date/time slot
        if 'scheduled_date' in request.data:
            connection.scheduled_date = request.data['scheduled_date']
        if 'pickup_time_slot' in request.data:
            connection.pickup_time_slot = request.data['pickup_time_slot']
        if 'courier_notes' in request.data:
            connection.courier_notes = request.data['courier_notes']

        connection.save()
        return Response(ConnectionSerializer(connection, context={'request': request}).data)

class ConnectionLocationView(APIView):
    permission_classes=[permissions.IsAuthenticated]
    def post(self,request,pk):
        try: c=Connection.objects.select_related('donor','receiver').get(pk=pk)
        except Connection.DoesNotExist: return Response({'error':'Connection not found.'},status=404)
        if request.user.id not in [c.donor_id,c.receiver_id] and request.user.role!='ADMIN': return Response({'error':'Permission denied.'},status=403)
        lat=request.data.get('latitude'); lng=request.data.get('longitude')
        if lat is None or lng is None: return Response({'error':'Latitude and longitude are required.'},status=400)
        address=str(request.data.get('address','')).strip()
        now = timezone.now()
        previous_share = c.location_shared_at
        if request.user.id==c.donor_id:
            c.donor_live_latitude=lat; c.donor_live_longitude=lng; c.donor_live_address=address; other=c.receiver
        else:
            c.receiver_live_latitude=lat; c.receiver_live_longitude=lng; c.receiver_live_address=address; other=c.donor
        c.location_shared_at=now; c.save()

        # Notify the other participant on the initial share, then at most once
        # every 15 minutes. Continuous GPS updates should never flood inboxes.
        should_email = previous_share is None or (now - previous_share).total_seconds() >= 900
        if should_email:
            maps=f'https://www.google.com/maps?q={lat},{lng}'
            send_platform_email(other.email,'Second Life - Live Pickup Location Shared',f'''Hello {other.name},

{request.user.name} has shared their current pickup/handover location for "{c.donation.title}".

Location: {address or f'{lat}, {lng}'}
Google Maps: {maps}

Please use the shared location only for arranging this Second Life handover.

Regards,
Second Life Team''')
        return Response(ConnectionSerializer(c,context={'request':request}).data)

class ConnectionCompleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        try:
            connection = (
                Connection.objects
                .select_for_update()
                .select_related(
                    'donation',
                    'donation__category',
                    'donor',
                    'receiver',
                    'delivery',
                    'request',
                )
                .prefetch_related('donation__images')
                .get(pk=pk)
            )
        except Connection.DoesNotExist:
            return Response(
                {'error': 'Connection not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if (
            request.user.role != 'ADMIN'
            and connection.donor_id != request.user.id
            and connection.receiver_id != request.user.id
        ):
            return Response(
                {'error': 'Permission denied.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Idempotent completion: a second click/retry must not create
        # duplicate notifications or duplicate completion emails.
        if connection.status == Connection.Status.COMPLETED:
            return Response({
                'message': 'This exchange has already been completed.',
                'connection': ConnectionSerializer(
                    connection,
                    context={'request': request},
                ).data,
            })

        now = timezone.now()
        connection.status = Connection.Status.COMPLETED
        connection.completed_at = now
        connection.save(
            update_fields=['status', 'completed_at', 'updated_at']
        )

        donation = connection.donation
        donation.status = Donation.Status.COMPLETED
        donation.save(update_fields=['status', 'updated_at'])

        # Keep the request lifecycle in sync with the connection.
        if connection.request_id:
            connection.request.status = DonationRequest.Status.COMPLETED
            connection.request.save(update_fields=['status', 'updated_at'])

        if hasattr(connection, 'delivery'):
            delivery = connection.delivery
            delivery.status = Delivery.DeliveryStatus.DELIVERED
            steps = delivery.timeline_steps or []
            now_str = now.strftime("%b %d, %Y %I:%M %p")
            for step in steps:
                step['status'] = 'COMPLETED'
                step['timestamp'] = step.get('timestamp') or now_str
            steps.append({
                'step': 'Impact Confirmed',
                'status': 'COMPLETED',
                'timestamp': now_str,
            })
            delivery.timeline_steps = steps
            delivery.save(update_fields=['status', 'timeline_steps', 'updated_at'])

        # In-app notifications.
        NotificationService.send(
            user=connection.donor,
            title="Donation Completed! 🎉",
            message=(
                f"'{donation.title}' has been successfully handed over to "
                f"{connection.receiver.name}. Thank you for making an impact!"
            ),
            notif_type="DONATION_DELIVERED",
            link=f"/donor/connections/{connection.id}",
        )
        NotificationService.send(
            user=connection.receiver,
            title="Exchange Completed! 💚",
            message=(
                f"You successfully received '{donation.title}' from "
                f"{connection.donor.name}. Give it a second life!"
            ),
            notif_type="DONATION_DELIVERED",
            link=f"/receiver/connections/{connection.id}",
        )

        timestamp = now.strftime("%B %d, %Y at %I:%M %p")

        donor_subject = "Second Life - Donation Successfully Completed"
        donor_message = f"""Hello {connection.donor.name},

Your donation has been successfully completed on Second Life.

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
Name: {connection.receiver.name}
Contact: {connection.receiver.phone or 'Not provided'}
Email: {connection.receiver.email}
Location: {connection.receiver.city or 'Not provided'}

Completion Details
------------------
Tracking Code: {getattr(connection.delivery, 'tracking_code', 'N/A')}
Completed At: {timestamp}
Status: Completed

The item has successfully reached its receiver and this exchange has been recorded in your impact history.

Thank you for helping give useful items a second life.

Regards,
Second Life Team

This is an automated email. Please do not reply directly to this message.
"""

        receiver_subject = "Second Life - Donation Successfully Received"
        receiver_message = f"""Hello {connection.receiver.name},

Your requested donation has been successfully completed on Second Life.

Donation Details
----------------
Item: {donation.title}
Category: {donation.category.name if donation.category else 'N/A'}
Condition: {donation.get_condition_display()}
Quantity: {donation.quantity}
Location: {donation.location}
City: {donation.city}

Donor Details
-------------
Name: {connection.donor.name}
Contact: {connection.donor.phone or 'Not provided'}
Email: {connection.donor.email}

Completion Details
------------------
Tracking Code: {getattr(connection.delivery, 'tracking_code', 'N/A')}
Completed At: {timestamp}
Status: Completed

Your receipt has been confirmed and this exchange has been added to your impact history.

Thank you for being part of Second Life.

Regards,
Second Life Team

This is an automated email. Please do not reply directly to this message.
"""

        send_platform_email(
            connection.donor.email,
            donor_subject,
            donor_message,
        )
        send_platform_email(
            connection.receiver.email,
            receiver_subject,
            receiver_message,
        )

        ActivityLog.objects.create(
            user=request.user,
            action="CONNECTION_COMPLETED",
            description=(
                f"Exchange completed for donation #{donation.id} "
                f"'{donation.title}' between {connection.donor.name} "
                f"and {connection.receiver.name}."
            ),
        )

        return Response({
            'message': 'Exchange marked as completed! Social & ecological impact recorded.',
            'connection': ConnectionSerializer(
                connection,
                context={'request': request},
            ).data,
        })


class AdminConnectionListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        queryset = Connection.objects.all().select_related(
            'donation', 'donation__category', 'donor', 'receiver', 'delivery'
        )
        status_param = request.query_params.get('status')
        if status_param and status_param.upper() != 'ALL':
            queryset = queryset.filter(status=status_param.upper())

        serializer = ConnectionSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
