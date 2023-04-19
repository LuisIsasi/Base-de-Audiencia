from .prod import *


# Cache
CACHES["default"]["KEY_PREFIX"] = "prod-a"
CACHES["default"]["LOCATION"] = "redis://aud01.geprod.amc:6379/1"

# Celery
BROKER_URL = CELERY_BROKER_URLS["prod-a"]
STATIC_ROOT = "/data/shared/assets/static/a"
STATIC_URL = "/static/a/"

LOGGING["handlers"]["sailthru_sync.tasks"][
    "filename"
] = "/data/local/log/sailthru_sync/tasks-a.log"
