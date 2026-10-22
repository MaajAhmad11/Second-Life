import os
from pathlib import Path
from datetime import timedelta
BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
except ImportError:
    pass


# ============================================================
# SECURITY
# ============================================================

SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-local-development-only-change-me'
)

DEBUG = os.environ.get(
    'DEBUG',
    'True'
) == 'True'

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,.onrender.com').split(',')
    if host.strip()
]

if '.onrender.com' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('.onrender.com')

if DEBUG and '*' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.extend(['localhost', '127.0.0.1'])


# ============================================================
# INSTALLED APPS
# ============================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',

    # SecondLife Apps
    'accounts.apps.AccountsConfig',
    'organizations.apps.OrganizationsConfig',
    'donations.apps.DonationsConfig',
    'item_requests.apps.ItemRequestsConfig',
    'connections.apps.ConnectionsConfig',
    'notifications.apps.NotificationsConfig',
    'dashboard.apps.DashboardConfig',
    'chatbot.apps.ChatbotConfig',
    'feedback.apps.FeedbackConfig',
]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
]

try:
    import whitenoise

    MIDDLEWARE.append(
        'whitenoise.middleware.WhiteNoiseMiddleware'
    )

except ImportError:
    pass

MIDDLEWARE.extend([
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
])


# ============================================================
# URL / TEMPLATES / WSGI
# ============================================================

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND':
            'django.template.backends.django.DjangoTemplates',

        'DIRS': [
            BASE_DIR / 'templates'
        ],

        'APP_DIRS': True,

        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# ============================================================
# AUTH USER
# ============================================================

AUTH_USER_MODEL = 'accounts.User'


# ============================================================
# DATABASE
# ============================================================

DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    ''
)

if (
    DATABASE_URL.startswith('postgres://')
    or
    DATABASE_URL.startswith('postgresql://')
):

    import urllib.parse

    url = urllib.parse.urlparse(
        DATABASE_URL
    )

    DATABASES = {
        'default': {
            'ENGINE':
                'django.db.backends.postgresql',

            'NAME':
                url.path[1:],

            'USER':
                url.username,

            'PASSWORD':
                url.password,

            'HOST':
                url.hostname,

            'PORT':
                url.port or 5432,
        }
    }

else:

    DATABASES = {
        'default': {
            'ENGINE':
                'django.db.backends.sqlite3',

            'NAME':
                BASE_DIR / 'db.sqlite3',
        }
    }


# ============================================================
# PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME':
            'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'
    },

    {
        'NAME':
            'django.contrib.auth.password_validation.MinimumLengthValidator',

        'OPTIONS': {
            'min_length': 8
        }
    },

    {
        'NAME':
            'django.contrib.auth.password_validation.CommonPasswordValidator'
    },

    {
        'NAME':
            'django.contrib.auth.password_validation.NumericPasswordValidator'
    },
]


# ============================================================
# INTERNATIONALIZATION
# ============================================================

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# ============================================================
# STATIC / MEDIA
# ============================================================

STATIC_URL = '/static/'

STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

FRONTEND_URL = os.environ.get(
    'FRONTEND_URL',
    'http://localhost:5173',
).strip().rstrip('/')


# ============================================================
# EMAIL - BREVO HTTPS API
# ============================================================

# Render Free blocks outbound SMTP ports. Second Life therefore sends
# transactional email through Brevo's HTTPS API instead.
#
# IMPORTANT:
# BREVO_API_KEY must exist only in the backend environment.
# Never put it in React/Vite/Vercel client-side code.

BREVO_API_KEY = os.environ.get(
    'BREVO_API_KEY',
    ''
).strip()

EMAIL_FROM_EMAIL = os.environ.get(
    'EMAIL_FROM_EMAIL',
    'givesthingsasecondlife@gmail.com'
).strip()

EMAIL_FROM_NAME = os.environ.get(
    'EMAIL_FROM_NAME',
    'Second Life'
).strip()

# Kept for compatibility with any existing code that reads this setting.
DEFAULT_FROM_EMAIL = EMAIL_FROM_EMAIL


# ============================================================
# OTP CONFIGURATION
# ============================================================

EMAIL_OTP_LENGTH = 6

EMAIL_OTP_EXPIRY_SECONDS = 90

EMAIL_OTP_MAX_ATTEMPTS = 5


# ============================================================
# REST FRAMEWORK
# ============================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),

    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),

    'DEFAULT_PAGINATION_CLASS':
        'rest_framework.pagination.PageNumberPagination',

    'PAGE_SIZE': 12,
}


# ============================================================
# SIMPLE JWT
# ============================================================

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':
        timedelta(days=7),

    'REFRESH_TOKEN_LIFETIME':
        timedelta(days=30),

    'ROTATE_REFRESH_TOKENS':
        True,

    'BLACKLIST_AFTER_ROTATION':
        False,

    'ALGORITHM':
        'HS256',

    'SIGNING_KEY':
        SECRET_KEY,

    'AUTH_HEADER_TYPES':
        ('Bearer',),

    'USER_ID_FIELD':
        'id',

    'USER_ID_CLAIM':
        'user_id',
}


# ============================================================
# CORS
# ============================================================

CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https:\/\/.*\.vercel\.app$",
]

CORS_ALLOWED_ORIGINS = [
    origin.strip().rstrip('/')
    for origin in os.environ.get(
        'CORS_ALLOWED_ORIGINS',
        'http://localhost:5173,http://127.0.0.1:5173,https://secondlife-platform.vercel.app',
    ).split(',')
    if origin.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip().rstrip('/')
    for origin in os.environ.get(
        'CSRF_TRUSTED_ORIGINS',
        'http://localhost:5173,http://127.0.0.1:5173,https://secondlife-platform.vercel.app',
    ).split(',')
    if origin.strip()
]

CORS_ALLOW_CREDENTIALS = True

# Optional persistent object storage for production media. Local development
# continues to use Django's filesystem storage when these values are absent.
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', '').strip()
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '').strip()
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '').strip()
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', '').strip()
AWS_S3_ENDPOINT_URL = os.environ.get('AWS_S3_ENDPOINT_URL', '').strip()

if AWS_STORAGE_BUCKET_NAME and AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    STORAGES = {
        'default': {
            'BACKEND': 'storages.backends.s3.S3Storage',
        },
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
        },
    }
    AWS_QUERYSTRING_AUTH = False
    AWS_DEFAULT_ACL = None
    AWS_S3_FILE_OVERWRITE = False
    AWS_S3_REGION_NAME = AWS_S3_REGION_NAME or None
    if AWS_S3_ENDPOINT_URL:
        AWS_S3_ENDPOINT_URL = AWS_S3_ENDPOINT_URL