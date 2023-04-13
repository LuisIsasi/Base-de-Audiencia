from datetime import datetime
from itertools import chain
from functools import wraps

from audb import celery_app
from celery.utils.log import get_task_logger
from django.core.cache import cache


class throttle(object):
    task_lock_prefix = "core::throttle::task::"
    queue_lock_prefix = "core::throttle::queue::"

    def __init__(self, interval_seconds, logger_name):
        assert interval_seconds > 0, "Interval seconds must be a positive value."
        self.interval_seconds = interval_seconds
        self.logger_name = logger_name

    def make_wrapped_key(self, func, *args, **kwargs):
        parts = chain(
            [func.__name__],
            args,
            ["{}::{}".format(key, value) for key, value in kwargs.items()]
        )
        return "::".join(map(str, parts))

    def __call__(self, f):
        @wraps(f)
        def wrapper(task, *args, **kwargs):
            logger = get_task_logger(self.logger_name)

            wrapped_key = self.make_wrapped_key(f, *args, **kwargs)
            task_lock = self.task_lock_prefix + wrapped_key
            now = int(datetime.now().timestamp())
            if cache.add(task_lock, now, self.interval_seconds):
                #  Task is not running so we can start it
                msg = "Throttle %s: Task %s starting (lock %s added)."
                logger.debug(msg, task.request.id, task.name, task_lock)

                return_value = f(task, *args, **kwargs)

                msg = "Throttle %s: Task %s finished (lock %s to expire naturally)."
                logger.debug(msg, task.request.id, task.name, task_lock)
                return return_value

            locked_time = cache.get(task_lock) or now
            delay = self.interval_seconds - (now - locked_time)
            if delay is None or delay < 1:
                delay = 1

            # Task is locked, so we can queue up the next guy
            queued_task_lock = self.queue_lock_prefix + wrapped_key
            if not cache.add(queued_task_lock, 1, delay):
                msg = "Throttle %s: Task %s already queued--nothing to do (lock %s already exists)."
                logger.debug(msg, task.request.id, task.name, queued_task_lock)
            else:
                celery_app.send_task(task.name, countdown=delay, args=args, kwargs=kwargs)
                msg = "Throttle %s: Task %s queued to run after %d seconds (lock %s added)."
                logger.debug(msg, task.request.id, task.name, delay, queued_task_lock)

        return wrapper
