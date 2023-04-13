from functools import wraps

from celery.exceptions import Retry
import sentry_sdk


class log_on_error(object):
    def __init__(self, error_msg, reraise=False):
        self.error_msg = error_msg
        self.reraise = reraise

    def __call__(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Retry:
                raise
            except Exception as e:
                sentry_sdk.capture_exception(e)
                if self.reraise:
                    raise
                return

        return wrapper
