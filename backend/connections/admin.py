from django.contrib import admin
from connections.models import Connection, Delivery

class DeliveryInline(admin.StackedInline):
    model = Delivery
    can_delete = False

@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'donation', 'donor', 'receiver', 'status', 'scheduled_date', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('donation__title', 'donor__name', 'receiver__name')
    ordering = ('-created_at',)
    inlines = [DeliveryInline]

@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('tracking_code', 'connection', 'status', 'courier_name', 'estimated_arrival')
    list_filter = ('status',)
    search_fields = ('tracking_code', 'courier_name')
