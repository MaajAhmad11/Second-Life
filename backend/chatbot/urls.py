from django.urls import path
from chatbot.views import ChatbotAssistantView

urlpatterns = [
    path('chat/', ChatbotAssistantView.as_view(), name='chatbot_assistant'),
]
