from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.urls import re_path

urlpatterns = [
    path('django-admin/', admin.site.urls),

    # SecondLife REST APIs
    path('api/', include('accounts.urls')),
    path('api/', include('organizations.urls')),
    path('api/', include('donations.urls')),
    path('api/', include('item_requests.urls')),
    path('api/', include('connections.urls')),
    path('api/', include('notifications.urls')),
    path('api/', include('dashboard.urls')),
    path('api/', include('chatbot.urls')),
    path('api/', include('feedback.urls')),
]

# Serve uploaded media in production as well as local development.
# For durable production storage, configure the optional S3-compatible
# storage variables in settings.
urlpatterns += [
    re_path(
        r'^media/(?P<path>.*)$',
        serve,
        {'document_root': settings.MEDIA_ROOT},
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
