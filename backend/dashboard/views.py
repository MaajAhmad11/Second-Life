from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta

from donations.models import Donation, Category
from item_requests.models import DonationRequest
from connections.models import Connection
from organizations.models import Organization
from dashboard.models import ActivityLog, ContactMessage, PlatformSetting
from dashboard.serializers import ActivityLogSerializer, ContactMessageSerializer
from donations.serializers import DonationListSerializer
from item_requests.serializers import DonationRequestSerializer
from accounts.permissions import IsAdmin

User = get_user_model()


class PublicStatsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        total_donations = Donation.objects.exclude(status__in=[Donation.Status.CANCELLED, Donation.Status.DRAFT]).count()
        active_donations = Donation.objects.filter(status=Donation.Status.AVAILABLE).count()
        active_donors = User.objects.filter(
            role='DONOR', is_active=True
        ).filter(
            Q(account_type='INDIVIDUAL') |
            Q(organization__verification_status=Organization.VerificationStatus.VERIFIED)
        ).distinct().count()
        receivers_helped = Connection.objects.filter(status=Connection.Status.COMPLETED).values('receiver_id').distinct().count()
        successful_connections = Connection.objects.filter(status=Connection.Status.COMPLETED).count()
        completed_connections = Connection.objects.filter(status=Connection.Status.COMPLETED).select_related('donation')
        completed_items = sum(int(c.donation.quantity or 0) for c in completed_connections)
        completed_weight_kg = sum(float(c.donation.total_weight_kg or 0) for c in completed_connections)
        return Response({
            'total_donations': total_donations,
            'active_donations': active_donations,
            'active_donors': active_donors,
            'receivers_helped': receivers_helped,
            'successful_connections': successful_connections,
            'communities_served': Organization.objects.filter(verification_status='VERIFIED').count(),
            'waste_diverted_kg': round(completed_weight_kg, 3),
            'lifetime_weight_kg': round(completed_weight_kg, 3),
        })


class DonorDashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        user_donations = Donation.objects.filter(donor=user)

        total_donations = user_donations.count()
        active_donations = user_donations.filter(
            status=Donation.Status.AVAILABLE
        ).count()

        matched_donations = user_donations.filter(
            status__in=[
                Donation.Status.PENDING,
                Donation.Status.MATCHED,
                Donation.Status.ACCEPTED,
                Donation.Status.IN_DELIVERY,
                Donation.Status.DELIVERED,
            ]
        ).count()

        completed_connections = Connection.objects.filter(
            donor=user,
            status=Connection.Status.COMPLETED,
        )

        completed_donations = user_donations.filter(
            status__in=[
                Donation.Status.DELIVERED,
                Donation.Status.COMPLETED,
            ]
        ).count()

        pending_requests = DonationRequest.objects.filter(
            donation__donor=user,
            status=DonationRequest.Status.PENDING,
        ).count()

        people_helped = completed_connections.values('receiver').distinct().count()
        successful_drops = completed_connections.count()

        completed_connection_list = list(completed_connections.select_related('donation'))
        items_reused = sum(int(c.donation.quantity or 0) for c in completed_connection_list)
        # Track the donor's entered weight immediately, including active/new donations.
        # This keeps My Impact live even before a handover is completed.
        weighted_donations = user_donations.filter(
            status__in=[
                Donation.Status.AVAILABLE,
                Donation.Status.PENDING,
                Donation.Status.MATCHED,
                Donation.Status.ACCEPTED,
                Donation.Status.IN_DELIVERY,
                Donation.Status.DELIVERED,
                Donation.Status.COMPLETED,
            ]
        )
        lifetime_weight_kg = sum(
            float(d.total_weight_kg or 0)
            for d in weighted_donations
        )
        co2_completed_weight_kg = sum(
            float(c.donation.total_weight_kg or 0)
            for c in completed_connection_list
        )
        co2_diverted_kg = round(co2_completed_weight_kg * 3.8, 1)

        recent_donations = (
            user_donations
            .select_related('category')
            .prefetch_related('images', 'requests')
            .order_by('-created_at')[:5]
        )

        recent_requests = (
            DonationRequest.objects
            .filter(donation__donor=user)
            .select_related(
                'donation',
                'donation__category',
                'receiver',
            )
            .prefetch_related('donation__images')
            .order_by('-created_at')[:5]
        )

        return Response({
            'total_donations': total_donations,
            'active_donations': active_donations,
            'matched_donations': matched_donations,
            'completed_donations': completed_donations,
            'pending_requests': pending_requests,
            'people_helped': people_helped,
            'co2_diverted_kg': co2_diverted_kg,
            'items_reused': items_reused,
            'lifetime_weight_kg': round(lifetime_weight_kg, 3),
            'successful_drops': successful_drops,
            'recent_donations': DonationListSerializer(
                recent_donations,
                many=True,
                context={'request': request},
            ).data,
            'recent_requests': DonationRequestSerializer(
                recent_requests,
                many=True,
                context={'request': request},
            ).data,
        })


class ReceiverDashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        my_requests = DonationRequest.objects.filter(receiver=user)

        total_requests = my_requests.count()
        active_requests = my_requests.filter(
            status=DonationRequest.Status.PENDING
        ).count()

        matched_requests = my_requests.filter(
            status__in=[
                DonationRequest.Status.APPROVED,
                DonationRequest.Status.MATCHED,
            ]
        ).count()

        completed_requests = my_requests.filter(
            status=DonationRequest.Status.COMPLETED
        ).count()

        completed_connections = Connection.objects.filter(
            receiver=user,
            status=Connection.Status.COMPLETED,
        )

        completed_connection_list = list(completed_connections.select_related('donation'))
        items_received = sum(int(c.donation.quantity or 0) for c in completed_connection_list)
        lifetime_weight_kg = sum(float(c.donation.total_weight_kg or 0) for c in completed_connection_list)

        ready_for_pickup = Connection.objects.filter(
            receiver=user,
            status__in=[
                Connection.Status.ACCEPTED,
                Connection.Status.IN_PROGRESS,
                Connection.Status.DELIVERED,
            ],
        ).count()

        waste_diverted_kg = round(lifetime_weight_kg, 3)

        recent_requests = (
            my_requests
            .select_related(
                'donation',
                'donation__category',
                'donation__donor',
            )
            .prefetch_related('donation__images')
            .order_by('-created_at')[:5]
        )

        return Response({
            'total_requests': total_requests,
            'active_requests': active_requests,
            'matched_requests': matched_requests,
            'completed_requests': completed_requests,
            'items_given_second_life': items_received,
            'ready_for_pickup': ready_for_pickup,
            'waste_diverted_kg': waste_diverted_kg,
            'lifetime_weight_kg': round(lifetime_weight_kg, 3),
            'recent_requests': DonationRequestSerializer(
                recent_requests,
                many=True,
                context={'request': request},
            ).data,
        })


class AdminDashboardStatsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        total_users = User.objects.count()
        total_donors = User.objects.filter(role='DONOR').count()
        total_receivers = User.objects.filter(role='RECEIVER').count()
        total_orgs = Organization.objects.count()
        pending_verifications = Organization.objects.filter(
            verification_status='PENDING'
        ).count()

        total_donations = Donation.objects.count()
        active_donations = Donation.objects.filter(
            status='AVAILABLE'
        ).count()

        pending_requests = DonationRequest.objects.filter(
            status='PENDING'
        ).count()

        successful_connections = Connection.objects.filter(
            status__in=[
                'ACCEPTED',
                'IN_PROGRESS',
                'DELIVERED',
                'COMPLETED'
            ]
        ).count()
        completed_items = Donation.objects.filter(status=Donation.Status.COMPLETED).aggregate(total=Sum('quantity')).get('total') or 0
        total_impact_kg = round(float(completed_items) * 3.8, 1)

        categories = Category.objects.annotate(
            count=Count('donations')
        )

        category_data = [
            {
                'name': c.name,
                'value': c.count
            }
            for c in categories
            if c.count > 0
        ]

        if not category_data:
            category_data = []

        # Build a real, database-backed 12-month trend.  The frontend polls this
        # endpoint, so new donations/users are reflected without a page reload.
        now = timezone.localtime(timezone.now()).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        months = []
        # Include the current month and the preceding 11 calendar months.
        for offset in range(11, -1, -1):
            month_index = now.year * 12 + (now.month - 1) - offset
            year, zero_based_month = divmod(month_index, 12)
            months.append(now.replace(year=year, month=zero_based_month + 1, day=1))

        monthly_donations = []
        user_growth = []
        for month in months:
            if month.month == 12:
                next_month = month.replace(year=month.year + 1, month=1)
            else:
                next_month = month.replace(month=month.month + 1)
            label = month.strftime('%b %Y')
            donation_count = Donation.objects.filter(created_at__gte=month, created_at__lt=next_month).count()
            completed_count = Connection.objects.filter(status=Connection.Status.COMPLETED, completed_at__gte=month, completed_at__lt=next_month).count()
            active_count = Donation.objects.filter(status=Donation.Status.AVAILABLE, created_at__lt=next_month).count()
            monthly_donations.append({
                'month': label,
                'donations': donation_count,
                'completed': completed_count,
                'active': active_count,
            })
            donor_count = User.objects.filter(role='DONOR', created_at__lt=next_month).count()
            receiver_count = User.objects.filter(role='RECEIVER', created_at__lt=next_month).count()
            user_growth.append({
                'month': label,
                'donors': donor_count,
                'receivers': receiver_count,
            })

        recent_activity = ActivityLog.objects.select_related(
            'user'
        )[:8]

        return Response({
            'overview': {
                'total_users': total_users,
                'total_donors': total_donors,
                'total_receivers': total_receivers,
                'total_organizations': total_orgs,
                'pending_verifications': pending_verifications,
                'total_donations': total_donations,
                'active_donations': active_donations,
                'pending_requests': pending_requests,
                'successful_connections': successful_connections,
                'completed_items': completed_items,
                'impact_kg': total_impact_kg,
            },
            'charts': {
                'donations_over_time': monthly_donations,
                'user_growth': user_growth,
                'category_distribution': category_data,
            },
            'recent_activity': ActivityLogSerializer(
                recent_activity,
                many=True
            ).data
        })


class AdminReportsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        period = request.query_params.get('period', '30d')
        from donations.models import Donation
        total_connections = Connection.objects.exclude(status=Connection.Status.CANCELLED).count()
        completed_connections = Connection.objects.filter(status=Connection.Status.COMPLETED).count()
        completion_rate = round((completed_connections / total_connections) * 100, 1) if total_connections else 0
        total_weight = sum(
            float(donation.total_weight_kg or 0)
            for donation in Donation.objects.filter(
                connections__status=Connection.Status.COMPLETED
            ).distinct().iterator()
        )
        from django.db.models import Avg, Count, Q
        breakdown = []
        categories = Category.objects.annotate(
            items=Count('donations', filter=~Q(donations__status__in=[Donation.Status.CANCELLED, Donation.Status.DRAFT]), distinct=True),
            delivered=Count('donations', filter=Q(donations__status__in=[Donation.Status.DELIVERED, Donation.Status.COMPLETED]), distinct=True),
        ).order_by('name')
        for category in categories:
            category_weight = sum(
                float(donation.total_weight_kg or 0)
                for donation in Donation.objects.filter(
                    category=category,
                    connections__status=Connection.Status.COMPLETED
                ).distinct().iterator()
            )
            breakdown.append({
                'category': category.name,
                'items': category.items,
                'delivered': category.delivered,
                'co2_kg': round(category_weight * 3.8, 1),
            })
        from feedback.models import Feedback
        avg_rating = Feedback.objects.aggregate(avg=Avg('rating'))['avg']
        return Response({
            'period': period,
            'metrics': {
                'completion_rate': f'{completion_rate}%',
                'average_match_time': None,
                'total_co2_offset_tonnes': round(total_weight * 3.8 / 1000, 3),
                'community_satisfaction': f'{avg_rating:.1f} / 5.0' if avg_rating is not None else None,
                'total_donations': Donation.objects.exclude(status__in=[Donation.Status.CANCELLED, Donation.Status.DRAFT]).count(),
                'completed_connections': completed_connections,
            },
            'breakdown_by_category': breakdown,
        })


class ContactMessageView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ContactMessageSerializer(
            data=request.data
        )

        if serializer.is_valid():
            msg = serializer.save()

            ActivityLog.objects.create(
                action="CONTACT_SUBMISSION",
                description=(
                    f"Public inquiry received from "
                    f"{msg.name} ({msg.email}): {msg.subject}"
                )
            )

            return Response(
                {
                    'message': (
                        'Thank you! Your inquiry has been received. '
                        'Our team will get back to you shortly.'
                    )
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def get(self, request):
        if not (
            request.user.is_authenticated
            and (
                request.user.role == 'ADMIN'
                or request.user.is_staff
            )
        ):
            return Response(
                {'error': 'Admin permission required.'},
                status=status.HTTP_403_FORBIDDEN
            )

        messages = ContactMessage.objects.all()

        return Response(
            ContactMessageSerializer(
                messages,
                many=True
            ).data
        )


class AdminActivityLogListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        logs = ActivityLog.objects.all().select_related(
            'user'
        )[:50]

        return Response(
            ActivityLogSerializer(
                logs,
                many=True
            ).data
        )


class AdminContactMessageDetailView(APIView):
    permission_classes = [IsAdmin]

    def patch(self, request, pk):
        try:
            msg = ContactMessage.objects.get(pk=pk)
        except ContactMessage.DoesNotExist:
            return Response(
                {'error': 'Message not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if 'is_resolved' in request.data:
            msg.is_resolved = bool(
                request.data['is_resolved']
            )

        if 'admin_notes' in request.data:
            msg.admin_notes = request.data['admin_notes']

        msg.save()

        return Response(
            ContactMessageSerializer(msg).data
        )

    def delete(self, request, pk):
        try:
            msg = ContactMessage.objects.get(pk=pk)
            msg.delete()

            return Response({
                'message': 'Message deleted successfully.'
            })

        except ContactMessage.DoesNotExist:
            return Response(
                {'error': 'Message not found'},
                status=status.HTTP_404_NOT_FOUND
            )


DEFAULT_SETTINGS = {
    'auto_matching_enabled': True,
    'auto_matching_threshold': 60,
    'require_org_verification': True,
    'max_active_requests_per_receiver': 5,
    'allow_anonymous_browsing': True,
    'maintenance_mode': False,
    'support_email': 'support@secondlife.eco',
    'impact_co2_factor': 3.5,
    'platform_name': 'SecondLife',
    'contact_phone': '+1 (206) 555-0192',
    'address': '742 Evergreen Terrace, Seattle, WA',
}


class AdminPlatformSettingsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        obj, _ = PlatformSetting.objects.get_or_create(
            key='system_config',
            defaults={'value': DEFAULT_SETTINGS}
        )

        current = {
            **DEFAULT_SETTINGS,
            **obj.value
        }

        return Response(current)

    def post(self, request):
        obj, _ = PlatformSetting.objects.get_or_create(
            key='system_config',
            defaults={'value': DEFAULT_SETTINGS}
        )

        merged = {
            **obj.value,
            **request.data
        }

        obj.value = merged
        obj.save()

        ActivityLog.objects.create(
            user=request.user,
            action="SYSTEM_SETTINGS_UPDATED",
            description=(
                f"System platform settings updated "
                f"by {request.user.email}"
            )
        )

        return Response({
            'message': 'Platform settings saved successfully.',
            'settings': obj.value
        })