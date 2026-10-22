from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q

from item_requests.models import DonationRequest
from item_requests.serializers import DonationRequestSerializer, DonationRequestCreateSerializer
from accounts.permissions import IsAdmin, IsDonor, IsReceiver
from services.connection_service import ConnectionService
from services.email_service import send_platform_email
from services.notification_service import NotificationService

class DonationRequestListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        queryset = DonationRequest.objects.all().select_related(
            'donation', 'donation__category', 'donation__donor', 'receiver'
        ).prefetch_related('donation__images')

        if user.role == 'DONOR':
            # Requests for donor's items
            queryset = queryset.filter(donation__donor=user)
        elif user.role == 'RECEIVER':
            # Requests submitted by receiver
            queryset = queryset.filter(receiver=user)
        # Admins can see all if they hit this, or use the admin endpoint

        status_param = request.query_params.get('status')
        if status_param and status_param.upper() != 'ALL':
            queryset = queryset.filter(status=status_param.upper())

        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(donation__title__icontains=search) |
                Q(receiver__name__icontains=search) |
                Q(message__icontains=search)
            )

        serializer = DonationRequestSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        if request.user.role not in ['RECEIVER', 'ADMIN']:
            return Response({'error': 'Only registered receivers can request items.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = DonationRequestCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            req = serializer.save()
            return Response(DonationRequestSerializer(req, context={'request': request}).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DonationRequestDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            req = DonationRequest.objects.select_related(
                'donation', 'donation__category', 'donation__donor', 'receiver'
            ).prefetch_related('donation__images').get(pk=pk)
        except DonationRequest.DoesNotExist:
            return Response({'error': 'Request not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Permission check
        if request.user.role != 'ADMIN' and req.receiver_id != request.user.id and req.donation.donor_id != request.user.id:
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        return Response(DonationRequestSerializer(req, context={'request': request}).data)

    def delete(self, request, pk):
        try:
            req = DonationRequest.objects.get(pk=pk)
        except DonationRequest.DoesNotExist:
            return Response({'error': 'Request not found.'}, status=status.HTTP_404_NOT_FOUND)

        if req.receiver != request.user and request.user.role != 'ADMIN':
            return Response({'error': 'You can only cancel your own requests.'}, status=status.HTTP_403_FORBIDDEN)

        if req.status != DonationRequest.Status.PENDING:
            return Response({'error': 'Only pending requests can be cancelled.'}, status=status.HTTP_400_BAD_REQUEST)

        req.status = DonationRequest.Status.CANCELLED
        req.save(update_fields=['status', 'updated_at'])

        NotificationService.send(
            user=req.donation.donor,
            title="Donation Request Cancelled",
            message=(
                f"{req.receiver.name} cancelled their request for "
                f"'{req.donation.title}'."
            ),
            notif_type="REQUEST_CANCELLED",
            link="/donor/requests",
        )

        send_platform_email(
            req.donation.donor.email,
            "Second Life - Donation Request Cancelled",
            (
                f"Hello {req.donation.donor.name},\n\n"
                f"{req.receiver.name} has cancelled their request for "
                f"'{req.donation.title}'.\n\n"
                "The item remains available if no other active request "
                "has been accepted.\n\n"
                "Regards,\nSecond Life Team\n\n"
                "This is an automated email. Please do not reply directly "
                "to this message.\n"
            ),
        )

        send_platform_email(
            req.receiver.email,
            "Second Life - Request Cancelled Successfully",
            (
                f"Hello {req.receiver.name},\n\n"
                f"Your request for '{req.donation.title}' has been "
                "cancelled successfully.\n\n"
                "You can continue browsing Second Life for other available items.\n\n"
                "Regards,\nSecond Life Team\n\n"
                "This is an automated email. Please do not reply directly "
                "to this message.\n"
            ),
        )

        return Response({'message': 'Request cancelled successfully.'})

class DonationRequestApproveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        scheduled_date = request.data.get('scheduled_date', 'Tomorrow, 10:00 AM')
        pickup_time_slot = request.data.get('pickup_time_slot', '10:00 AM - 12:00 PM')
        notes = request.data.get('notes', '')

        try:
            connection = ConnectionService.approve_request(
                donation_request_id=pk,
                donor_user=request.user,
                scheduled_date=scheduled_date,
                pickup_time_slot=pickup_time_slot,
                notes=notes
            )
            return Response({
                'message': 'Request approved and connection established! 🎉',
                'connection_id': connection.id
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class DonationRequestRejectView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        reason = request.data.get('reason', '')
        try:
            req = ConnectionService.reject_request(
                donation_request_id=pk,
                donor_user=request.user,
                reason=reason
            )
            return Response({
                'message': 'Request declined.',
                'status': req.status
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class AdminRequestListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        queryset = DonationRequest.objects.all().select_related(
            'donation', 'donation__donor', 'receiver'
        )

        status_param = request.query_params.get('status')
        if status_param and status_param.upper() != 'ALL':
            queryset = queryset.filter(status=status_param.upper())

        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(donation__title__icontains=search) |
                Q(receiver__name__icontains=search) |
                Q(donation__donor__name__icontains=search)
            )

        serializer = DonationRequestSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
