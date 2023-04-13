from .base import *


DATABASES['default']['NAME'] = 'circle_test'
DATABASES['default']['USER'] = 'ubuntu'
DATABASES['default']['PASSWORD'] = ''

RAVEN_CONFIG['dsn'] = None

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
