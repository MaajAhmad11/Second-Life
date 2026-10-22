from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from accounts.models import User, Profile

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'name', 'role', 'account_type', 'city', 'is_verified', 'is_active', 'created_at')
    list_filter = ('role', 'account_type', 'is_verified', 'is_active', 'city')
    search_fields = ('email', 'name', 'city', 'phone')
    ordering = ('-created_at',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('name', 'phone', 'address', 'city', 'country')}),
        ('Role & Verification', {'fields': ('role', 'account_type', 'is_verified', 'is_active')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'pickup_radius', 'handover_preference', 'updated_at')
    search_fields = ('user__email', 'user__name')
