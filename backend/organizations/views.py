from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q

from organizations.models import Organization
from organizations.serializers import OrganizationSerializer, OrganizationReviewSerializer
from accounts.permissions import IsAdmin
from services.verification_service import VerificationService

class OrganizationProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            org = Organization.objects.get(user=request.user)
            return Response(OrganizationSerializer(org).data)
        except Organization.DoesNotExist:
            return Response({'error': 'No organization associated with this account.'}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request):
        try:
            org = Organization.objects.get(user=request.user)
        except Organization.DoesNotExist:
            return Response({'error': 'No organization associated with this account.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = OrganizationSerializer(org, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrganizationPublicListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        orgs = Organization.objects.filter(verification_status='VERIFIED')
        return Response(OrganizationSerializer(orgs, many=True).data)

class AdminOrganizationListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        queryset = Organization.objects.all().select_related('user')

        status_param = request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(verification_status=status_param.upper())

        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(organization_name__icontains=search) |
                Q(contact_person__icontains=search) |
                Q(license_number__icontains=search) |
                Q(city__icontains=search)
            )

        serializer = OrganizationSerializer(queryset, many=True)
        return Response(serializer.data)

class AdminOrganizationDetailView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request, pk):
        try:
            org = Organization.objects.select_related('user').prefetch_related('verifications').get(pk=pk)
            return Response(OrganizationSerializer(org).data)
        except Organization.DoesNotExist:
            return Response({'error': 'Organization not found'}, status=status.HTTP_404_NOT_FOUND)

class AdminOrganizationVerifyView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        serializer = OrganizationReviewSerializer(data=request.data)
        if serializer.is_valid():
            try:
                org = VerificationService.review_organization(
                    org_id=pk,
                    admin_user=request.user,
                    action=serializer.validated_data['action'],
                    notes=serializer.validated_data.get('notes', '')
                )
                return Response({
                    'message': f"Organization successfully {serializer.validated_data['action'].lower()}.",
                    'organization': OrganizationSerializer(org).data
                })
            except Organization.DoesNotExist:
                return Response({'error': 'Organization not found'}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
