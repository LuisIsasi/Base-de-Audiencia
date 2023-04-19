import random
import string


def generate_random_string(length):
    choices = string.ascii_lowercase + string.digits
    items = [random.SystemRandom().choice(choices) for _ in range(length)]
    return "".join(items)


def generate_email():
    parts = [
        generate_random_string(random.randrange(1, 50)),
        "@",
        generate_random_string(random.randrange(1, 50)),
        ".",
        generate_random_string(random.randrange(1, 50)),
    ]
    return "".join(parts)


MOMMY_CUSTOM_FIELDS_GEN = {
    "django.db.models.EmailField": generate_email,
}
