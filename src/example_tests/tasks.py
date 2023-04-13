from audb import celery_app


@celery_app.task()
def return_noodles():
    return "noodles"
