from django.db import models


class ChatbotFAQ(models.Model):
    CATEGORY_CHOICES = [
        ("general", "General"),
        ("donations", "Donations"),
        ("requests", "Requests"),
        ("accounts", "Accounts"),
        ("organizations", "Organizations"),
        ("matching", "Matching"),
        ("delivery", "Delivery"),
        ("safety", "Safety"),
        ("technical", "Technical"),
        ("team", "Team"),
    ]

    question = models.CharField(max_length=500)

    answer = models.TextField()

    keywords = models.TextField(
        blank=True,
        help_text="Separate keywords with commas. Example: donate, donation, give"
    )

    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default="general"
    )

    is_active = models.BooleanField(default=True)

    priority = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-priority", "question"]

    def __str__(self):
        return self.question
