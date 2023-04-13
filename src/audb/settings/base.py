import os

from google_auth.settings import *

from .celery import *
from .model_mommy import MOMMY_CUSTOM_FIELDS_GEN
from .sailthru import *

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '12_gu_t8tsav2r0v@z7y8*timv4=2(hbf0h(8y-@a=#@=l^_(m'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

BASE_URL = 'http://localhost:7979'
ALLOWED_HOSTS = []

SECURE_HSTS_SECONDS = 31536000
SECURE_CONTENT_TYPE_NOSNIFF = True  # We should also set this in nginx
SECURE_BROWSER_XSS_FILTER = True
SECURE_SSL_REDIRECT = False  # setting to True causes a redirect loop on prod, prob b/c of nginx
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False

# If there are any places in the future we wish to be exempt, django provides a
# decorator for this purpose
X_FRAME_OPTIONS = 'DENY'


# Application definition

INSTALLED_APPS = [
    'google_auth',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_extensions',
    'djcelery',
    'rest_framework',
    'rest_framework.authtoken',
    'social.apps.django_app.default',

    'core.apps.CoreConfig',  # must come after what precedes for admin config to happen
    'sailthru_sync.apps.SailthruSyncConfig',
    'example_tests.apps.ExampleTestsConfig',
    'debug_toolbar',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'google_auth.middleware.GoogleAuthExceptionMiddleware',
]

ROOT_URLCONF = 'audb.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social.apps.django_app.context_processors.backends',
                'social.apps.django_app.context_processors.login_redirect',
            ],
        },
    },
]

WSGI_APPLICATION = 'audb.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'audb',
        'USER': 'django',
        'PASSWORD': 'django',  # not actually the password; Postgres is config'd for local access
        'HOST': 'db',
        'PORT': '5432'
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/New_York'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'

# Cache
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://redis:6379/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
}

# Email

EMAIL_HOST = 'relay1.geprod.amc'
DEFAULT_FROM_EMAIL = 'no-reply@govexec.com'


# Celery
BROKER_URL = CELERY_BROKER_URLS['dev']
CELERY_PROJECT_NAME = 'audb'


# Logging

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'debug_format': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S",
        },
    },
    'handlers': {
        'sailthru_sync.tasks': {
            'level': 'DEBUG',
            'class': 'core.logging.WatchedFileHandler',
            'filename': '/tmp/sailthru_sync.tasks.log',
            'formatter': 'debug_format',
        }
    },
    'loggers': {
        'sailthru_sync.tasks': {
            'handlers': ['sailthru_sync.tasks'],
            'level': 'DEBUG',
            'propagate': True,
        }
    },
}

# Sentry

RAVEN_CONFIG = {
    'dsn': 'http://5b35e023668542a19ea102f986a70a3d:9292b78557e24dcb8352a13f5d6ecdaa@sentry01.geprod.amc/17'
}


# Social Auth
AUTHENTICATION_BACKENDS = (
    'google_auth.backends.GoogleAuthBackend',
)

SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/'
SOCIAL_AUTH_LOGIN_ERROR_URL = '/'
SOCIAL_AUTH_GOOGLE_AUTH_WHITELISTED_DOMAINS = (
    'atlanticmedia.com',
    'atlanticmediacompany.com',
    'defenseone.com',
    'govexec.com',
    'nationaljournal.com',
    'nextgov.com',
    'theatlantic.com',
    'govexecmediagroup.com',
)
SOCIAL_AUTH_REDIRECT_IS_HTTPS = False
SOCIAL_AUTH_ON_HTTPS = False
SOCIAL_AUTH_GOOGLE_AUTH_KEY = '929348258608-g8sud34o16lqd8j4g07gpm0f55m5o849.apps.googleusercontent.com'
SOCIAL_AUTH_GOOGLE_AUTH_SECRET = 'chyWjpWIop2HTorv6wUkHpnL'
SOCIAL_AUTH_URL_NAMESPACE = 'google-auth:social'


# Django REST Framework

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
    'PAGE_SIZE': 10
}


# Django Debug Toolbar

def custom_show_toolbar(self):
    if os.environ.get('DJANGO_TEST'):
        return False
    else:
        from django.conf import settings
        return settings.ENABLE_DEBUG_TOOLBAR

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': custom_show_toolbar,
}

ENABLE_DEBUG_TOOLBAR = False

# Sailthru
SAILTHRU_API_KEY = SAILTHRU_CONFIG['dev']['key']
SAILTHRU_API_SECRET = SAILTHRU_CONFIG['dev']['secret']
