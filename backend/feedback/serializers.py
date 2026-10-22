from rest_framework import serializers
from .models import Feedback
class FeedbackSerializer(serializers.ModelSerializer):
    author_name=serializers.CharField(source='author.name',read_only=True)
    class Meta:
        model=Feedback
        fields=['id','rating','comment','author_name','created_at']
        read_only_fields=['id','author_name','created_at']
