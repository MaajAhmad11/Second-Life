from django.contrib import admin
from donations.models import Category, Donation, DonationImage, SavedItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

class DonationImageInline(admin.TabularInline):
    model = DonationImage
    extra = 1

@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('title', 'donor', 'category', 'condition', 'city', 'status', 'created_at')
    list_filter = ('status', 'category', 'condition', 'delivery_option', 'city')
    search_fields = ('title', 'description', 'donor__name', 'donor__email', 'location')
    ordering = ('-created_at',)
    inlines = [DonationImageInline]

@admin.register(SavedItem)
class SavedItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'donation', 'created_at')
    search_fields = ('user__name', 'donation__title')
