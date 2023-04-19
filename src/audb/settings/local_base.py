from .base import *

# Cache
CACHES["default"]["KEY_PREFIX"] = "local"

# Celery
BROKER_URL = CELERY_BROKER_URLS["local"]

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

ENABLE_DEBUG_TOOLBAR = True

INTERNAL_IPS = [
    "::1",
    "127.0.0.1",
    "::ffff:10.0.2.2",
]
