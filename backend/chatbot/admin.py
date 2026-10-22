from django.contrib import admin
from .models import ChatbotFAQ


@admin.register(ChatbotFAQ)
class ChatbotFAQAdmin(admin.ModelAdmin):
    list_display = (
        "question",
        "category",
        "is_active",
        "priority",
        "updated_at",
    )

    list_filter = (
        "category",
        "is_active",
    )

    search_fields = (
        "question",
        "answer",
        "keywords",
    )

    list_editable = (
        "is_active",
        "priority",
    )

    ordering = (
        "-priority",
        "question",
    )
