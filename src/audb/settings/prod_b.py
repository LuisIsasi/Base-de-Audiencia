from .prod import *


# Cache
CACHES["default"]["KEY_PREFIX"] = "prod-b"
CACHES["default"]["LOCATION"] = "redis://aud01.geprod.amc:6379/2"

# Celery
BROKER_URL = CELERY_BROKER_URLS["prod-b"]
STATIC_ROOT = "/data/shared/assets/static/b"
STATIC_URL = "/static/b/"

LOGGING["handlers"]["sailthru_sync.tasks"][
    "filename"
] = "/data/local/log/sailthru_sync/tasks-b.log"
