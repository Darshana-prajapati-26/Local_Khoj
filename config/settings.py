"""
Local Khoj — Django Settings
Reads all secrets from .env via python-decouple.
"""
from pathlib import Path
from decouple import config, Csv
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# ===========================
# CORE
# ===========================
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-only-change-me')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())

# ===========================
# SECURITY
# ===========================
SECURE_HSTS_SECONDS          = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD          = not DEBUG
CSRF_COOKIE_SECURE           = not DEBUG
SESSION_COOKIE_SECURE        = not DEBUG
CSRF_COOKIE_HTTPONLY         = True
SESSION_COOKIE_HTTPONLY      = True
X_FRAME_OPTIONS              = 'DENY'
SECURE_BROWSER_XSS_FILTER   = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER      = ('HTTP_X_FORWARDED_PROTO', 'https') if not DEBUG else None

# ===========================
# INSTALLED APPS
# ===========================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.sites',

    # Third-party
    'rest_framework',
    'corsheaders',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_filters',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    # Project apps
    'accounts',
    'core',
    'stores',
    'products',
    'services',
    'cart',
    'orders',
    'vendor_panel',
    'admin_panel',
]

# ===========================
# MIDDLEWARE
# ===========================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ===========================
# URLS & TEMPLATES
# ===========================
ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.global_data',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ===========================
# DATABASE
# ===========================
# Priority: DATABASE_URL (Render/production) > MySQL > SQLite (local dev)
_DATABASE_URL = config('DATABASE_URL', default='')

if _DATABASE_URL:
    # Render (and other platforms) inject DATABASE_URL automatically
    DATABASES = {
        'default': dj_database_url.parse(
            _DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    USE_MYSQL = config('USE_MYSQL', default=False, cast=bool)
    if USE_MYSQL:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': config('DB_NAME', default='local_khoj_db'),
                'USER': config('DB_USER', default='root'),
                'PASSWORD': config('DB_PASSWORD', default=''),
                'HOST': config('DB_HOST', default='127.0.0.1'),
                'PORT': config('DB_PORT', default='3306'),
                'OPTIONS': {
                    'charset': 'utf8mb4',
                    'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                },
                'CONN_MAX_AGE': 600,
            }
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }

# ===========================
# PASSWORD VALIDATION
# ===========================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ===========================
# AUTHENTICATION
# ===========================
AUTH_USER_MODEL    = 'accounts.User'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'
LOGIN_URL          = 'login'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

# ===========================
# ALLAUTH / GOOGLE OAUTH
# ===========================
ACCOUNT_EMAIL_REQUIRED          = True
ACCOUNT_USERNAME_REQUIRED       = True
ACCOUNT_AUTHENTICATION_METHOD  = 'username_email'
ACCOUNT_EMAIL_VERIFICATION      = 'optional'
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
SOCIALACCOUNT_AUTO_SIGNUP       = True
SOCIALACCOUNT_LOGIN_ON_GET      = True

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'APP': {
            'client_id': config('GOOGLE_CLIENT_ID', default=''),
            'secret':    config('GOOGLE_CLIENT_SECRET', default=''),
            'key': '',
        }
    }
}

# ===========================
# OTP / 2FA
# ===========================
OTP_EXPIRY_MINUTES = 10
OTP_MAX_ATTEMPTS   = 3

# ===========================
# INTERNATIONALISATION
# ===========================
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'Asia/Kolkata'
USE_I18N      = True
USE_TZ        = True

# ===========================
# STATIC & MEDIA
# ===========================
STATIC_URL       = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT      = BASE_DIR / 'staticfiles'
MEDIA_URL        = '/media/'
MEDIA_ROOT       = BASE_DIR / 'media'

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ===========================
# CACHING
# — Uses Redis if REDIS_URL is set, otherwise falls back to
#   database cache (no Redis server required in development)
# ===========================
_REDIS_URL = config('REDIS_URL', default='')

if _REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': _REDIS_URL,
            'KEY_PREFIX': 'local_khoj',
            'TIMEOUT': 3600,
        }
    }
else:
    # Fallback: database cache — works with zero extra services
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'django_cache_table',
        }
    }

# ===========================
# SESSION
# ===========================
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # 2 weeks

# ===========================
# REST FRAMEWORK
# ===========================
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
}

# ===========================
# CRISPY FORMS
# ===========================
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK          = 'bootstrap5'

# ===========================
# CORS
# ===========================
CORS_ALLOWED_ORIGINS  = config('CORS_ALLOWED_ORIGINS', default='http://localhost:3000', cast=Csv())
CORS_ALLOW_CREDENTIALS = True

# ===========================
# EMAIL
# ===========================
EMAIL_BACKEND       = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST          = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT          = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS       = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER     = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL  = config('DEFAULT_FROM_EMAIL', default='noreply@localkhoj.com')
SERVER_EMAIL        = DEFAULT_FROM_EMAIL

# Email admins on 500 errors (only when DEBUG=False)
_admin_emails = config('ADMIN_EMAILS', default='', cast=Csv())
ADMINS = []
for entry in _admin_emails:
    if ':' in entry:
        name, email = entry.split(':', 1)
        ADMINS.append((name.strip(), email.strip()))

# ===========================
# PAYMENTS
# ===========================
RAZORPAY_KEY_ID      = config('RAZORPAY_KEY_ID', default='')
RAZORPAY_KEY_SECRET  = config('RAZORPAY_KEY_SECRET', default='')
STRIPE_SECRET_KEY    = config('STRIPE_SECRET_KEY', default='')
STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_WEBHOOK_SECRET  = config('STRIPE_WEBHOOK_SECRET', default='')

# ===========================
# EXTERNAL SERVICES
# ===========================
GOOGLE_MAPS_API_KEY  = config('GOOGLE_MAPS_API_KEY', default='')
RECAPTCHA_SITE_KEY   = config('RECAPTCHA_SITE_KEY', default='')
RECAPTCHA_SECRET_KEY = config('RECAPTCHA_SECRET_KEY', default='')

# ===========================
# LOGGING
# ===========================
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} — {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {'()': 'django.utils.log.RequireDebugFalse'},
        'require_debug_true':  {'()': 'django.utils.log.RequireDebugTrue'},
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'django.log',
            'maxBytes': 1024 * 1024 * 15,  # 15 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'mail_admins'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['file', 'mail_admins'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# ===========================
# CELERY (optional — only if Redis is configured)
# ===========================
CELERY_BROKER_URL      = config('REDIS_URL', default='redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND  = config('REDIS_URL', default='redis://127.0.0.1:6379/0')
CELERY_ACCEPT_CONTENT  = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE        = 'Asia/Kolkata'

# ===========================
# APP SETTINGS
# ===========================
MAX_UPLOAD_SIZE        = 5 * 1024 * 1024   # 5 MB
ALLOWED_IMAGE_TYPES    = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg']
DEFAULT_LISTING_DURATION = 365
LISTINGS_PER_PAGE      = 20
LEADS_RETENTION_DAYS   = 90
REVIEW_MODERATION_ENABLED = True
MINIMUM_REVIEW_LENGTH  = 10
MIN_SEARCH_LENGTH      = 2
MAX_SEARCH_RESULTS     = 100
PAGINATION_SIZE        = 20
