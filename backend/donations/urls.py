from django.urls import path
from donations.views import (
    CategoryListView, DonationListView, DonationDetailView,
    MyDonationsListView, RecommendedDonationsView,
    SavedItemToggleView, SavedItemListView, UploadDonationImageView,
    AdminDonationListView
)

urlpatterns = [
    path('categories/', CategoryListView.as_view(), name='categories_list'),
    path('donations/', DonationListView.as_view(), name='donations_list'),
    path('donations/my/', MyDonationsListView.as_view(), name='my_donations_list'),
    path('donations/recommended/', RecommendedDonationsView.as_view(), name='recommended_donations'),
    path('donations/upload-image/', UploadDonationImageView.as_view(), name='upload_image'),
    path('donations/<int:pk>/', DonationDetailView.as_view(), name='donation_detail'),
    path('donations/<int:pk>/save/', SavedItemToggleView.as_view(), name='save_donation_toggle'),
    path('saved-items/', SavedItemListView.as_view(), name='saved_items_list'),

    # Admin
    path('admin/donations/', AdminDonationListView.as_view(), name='admin_donations_list'),
]
