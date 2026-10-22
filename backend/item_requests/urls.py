from django.urls import path
from item_requests.views import (
    DonationRequestListCreateView, DonationRequestDetailView,
    DonationRequestApproveView, DonationRequestRejectView, AdminRequestListView
)

urlpatterns = [
    path('requests/', DonationRequestListCreateView.as_view(), name='requests_list_create'),
    path('requests/<int:pk>/', DonationRequestDetailView.as_view(), name='request_detail'),
    path('requests/<int:pk>/approve/', DonationRequestApproveView.as_view(), name='request_approve'),
    path('requests/<int:pk>/reject/', DonationRequestRejectView.as_view(), name='request_reject'),

    # Admin
    path('admin/requests/', AdminRequestListView.as_view(), name='admin_requests_list'),
]
