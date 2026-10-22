from django.urls import path
from dashboard.views import (
    PublicStatsView, DonorDashboardStatsView, ReceiverDashboardStatsView,
    AdminDashboardStatsView, AdminReportsView, ContactMessageView, AdminActivityLogListView,
    AdminContactMessageDetailView, AdminPlatformSettingsView
)

urlpatterns = [
    path('stats/public/', PublicStatsView.as_view(), name='public_stats'),
    path('stats/donor/', DonorDashboardStatsView.as_view(), name='donor_stats'),
    path('stats/receiver/', ReceiverDashboardStatsView.as_view(), name='receiver_stats'),
    path('contact/', ContactMessageView.as_view(), name='contact_message'),

    # Admin
    path('admin/dashboard/', AdminDashboardStatsView.as_view(), name='admin_dashboard_stats'),
    path('admin/reports/', AdminReportsView.as_view(), name='admin_reports'),
    path('admin/activity/', AdminActivityLogListView.as_view(), name='admin_activity_logs'),
    path('admin/messages/', ContactMessageView.as_view(), name='admin_contact_messages'),
    path('admin/messages/<int:pk>/', AdminContactMessageDetailView.as_view(), name='admin_contact_message_detail'),
    path('admin/settings/', AdminPlatformSettingsView.as_view(), name='admin_platform_settings'),
]
