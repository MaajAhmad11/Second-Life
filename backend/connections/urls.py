from django.urls import path
from connections.views import (
    ConnectionListView, ConnectionDetailView, ConnectionCompleteView, ConnectionLocationView, AdminConnectionListView
)

urlpatterns = [
    path('connections/', ConnectionListView.as_view(), name='connections_list'),
    path('connections/<int:pk>/', ConnectionDetailView.as_view(), name='connection_detail'),
    path('connections/<int:pk>/complete/', ConnectionCompleteView.as_view(), name='connection_complete'),
    path('connections/<int:pk>/location/', ConnectionLocationView.as_view(), name='connection_location'),

    # Admin
    path('admin/connections/', AdminConnectionListView.as_view(), name='admin_connections_list'),
]
