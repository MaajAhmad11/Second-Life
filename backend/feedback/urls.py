from django.urls import path
from .views import FeedbackListCreateView
urlpatterns=[path('connections/<int:connection_id>/feedback/',FeedbackListCreateView.as_view())]
