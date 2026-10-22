from django.contrib import admin
from .models import Feedback
@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display=('id','connection','author','rating','created_at')
    list_filter=('rating','created_at')
    search_fields=('author__email','author__name','connection__donation__title','comment')
