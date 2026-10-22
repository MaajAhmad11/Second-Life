from django.urls import path
from organizations.views import (
    OrganizationProfileView, OrganizationPublicListView,
    AdminOrganizationListView, AdminOrganizationDetailView, AdminOrganizationVerifyView
)

urlpatterns = [
    path('organizations/me/', OrganizationProfileView.as_view(), name='org_profile'),
    path('organizations/public/', OrganizationPublicListView.as_view(), name='org_public_list'),

    # Admin endpoints
    path('admin/organizations/', AdminOrganizationListView.as_view(), name='admin_orgs_list'),
    path('admin/organizations/<int:pk>/', AdminOrganizationDetailView.as_view(), name='admin_org_detail'),
    path('admin/organizations/<int:pk>/verify/', AdminOrganizationVerifyView.as_view(), name='admin_org_verify'),
]
