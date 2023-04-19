import sentry_sdk

from .base import *


sentry_sdk.init(
    dsn="https://10a1e34a7d204746a4d11eb9403d4b7e@o507832.ingest.sentry.io/5599534",
    environment="development",
    traces_sample_rate=1.0,
    send_default_pii=True,
)

BASE_URL = "https://dev-audb.govexec.com"

ALLOWED_HOSTS = [
    "dev.audb.govexec.com",
    "dev-audb.govexec.com",
]

DATABASES["default"]["HOST"] = "pgsql.gedev.amc"
DATABASES["default"]["PASSWORD"] = "Tt?P7DX8"

RAVEN_CONFIG[
    "dsn"
] = "http://5b35e023668542a19ea102f986a70a3d:9292b78557e24dcb8352a13f5d6ecdaa@sentry01.geprod.amc/17"

# Social Auth
SOCIAL_AUTH_REDIRECT_IS_HTTPS = True
SOCIAL_AUTH_ON_HTTPS = True

# Cache
CACHES["default"]["KEY_PREFIX"] = "dev"
CACHES["default"]["LOCATION"] = "redis://aud01.gedev.amc:6379/1"

# Celery
BROKER_URL = CELERY_BROKER_URLS["dev"]
STATIC_ROOT = "/data/shared/assets/static/a"
STATIC_URL = "/static/a/"

LOGGING["handlers"]["sailthru_sync.tasks"][
    "filename"
] = "/data/local/log/sailthru_sync/tasks.log"
