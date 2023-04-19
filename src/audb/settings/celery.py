from urllib.parse import quote


CELERY_BROKER_URLS = {
    "local": "redis://redis:6379/0",
    "dev": "amqp://audb-a:{}@aud-jobs01.gedev.amc/audb-a".format(
        quote("Is{momofoku}Better[than]Daikaya?")
    ),
    "prod-a": "amqp://audb-a:{}@aud-jobs01.geprod.amc/audb-a".format(
        quote("Is{momofoku}Better[than]Daikaya?")
    ),
    "prod-b": "amqp://audb-b:{}@aud-jobs01.geprod.amc/audb-b".format(
        quote("I{wanna}Eat[me]Some|kabob:Palace!")
    ),
}
## Using the database to store task state and results.
CELERY_RESULT_BACKEND = "djcelery.backends.database:DatabaseBackend"
CELERY_RESULT_PERSISTENT = True  # Maybe we should discuss?
CELERY_SEND_TASK_ERROR_EMAILS = True
CELERY_SEND_EVENTS = True
CELERY_SEND_TASK_SENT_EVENT = True
CELERYBEAT_SCHEDULER = "djcelery.schedulers.DatabaseScheduler"
