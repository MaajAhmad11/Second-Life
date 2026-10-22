from django.contrib import admin
from item_requests.models import DonationRequest

@admin.register(DonationRequest)
class DonationRequestAdmin(admin.ModelAdmin):
    list_display = ('donation', 'receiver', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('donation__title', 'receiver__name', 'receiver__email', 'message')
    ordering = ('-created_at',)
