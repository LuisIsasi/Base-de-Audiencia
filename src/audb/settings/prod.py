import sentry_sdk

from .base import *


sentry_sdk.init(
    dsn="https://10a1e34a7d204746a4d11eb9403d4b7e@o507832.ingest.sentry.io/5599534",
    environment="production",
    traces_sample_rate=0.1,  # Don't increase. We are billed by sample count.
    send_default_pii=True,
)

DEBUG = False

BASE_URL = "https://audb.govexec.com"

ALLOWED_HOSTS = [
    "aud01.geprod.amc",
    "audb.govexec.com",
    "stage.audb.govexec.com",
]

DATABASES["default"]["HOST"] = "pgsql.geprod.amc"
DATABASES["default"]["PASSWORD"] = "Tt?P7DX8"

RAVEN_CONFIG[
    "dsn"
] = "http://9978b58ef4fc4d908f55f2bcb7317872:f7f3b657c3b0489b8e7f40bf16b08872@sentry01.geprod.amc/18"

# Social Auth
SOCIAL_AUTH_REDIRECT_IS_HTTPS = True
SOCIAL_AUTH_ON_HTTPS = True

# Sailthru
SAILTHRU_API_KEY = SAILTHRU_CONFIG["prod"]["key"]
SAILTHRU_API_SECRET = SAILTHRU_CONFIG["prod"]["secret"]
