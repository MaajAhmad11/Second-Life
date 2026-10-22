from django.urls import path
from notifications.views import NotificationListView, NotificationMarkReadView, NotificationMarkAllReadView

urlpatterns = [
    path('notifications/', NotificationListView.as_view(), name='notifications_list'),
    path('notifications/mark-all-read/', NotificationMarkAllReadView.as_view(), name='notifications_mark_all_read'),
    path('notifications/<int:pk>/read/', NotificationMarkReadView.as_view(), name='notification_mark_read'),
]
