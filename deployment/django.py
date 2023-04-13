import os
from functools import wraps

from fabric import api as fab

from .command import Command, from_basedir


def with_env(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        environment = {
            'DJANGO_SETTINGS_MODULE': self.conf,
        }

        with fab.prefix("source " + self.virtualenv_bin), fab.shell_env(**environment):
            return f(self, *args, **kwargs)

    return wrapper


class Django(Command):
    DEV_CONF = 'audb.settings.dev'
    A_VERSION_CONF = 'audb.settings.prod_a'
    B_VERSION_CONF = 'audb.settings.prod_b'

    def __init__(self, dev=True, project_version='a', *args, **kwargs):
        super(Django, self).__init__(*args, **kwargs)
        assert project_version in ['a', 'b']

        self.project_version = project_version

        if dev:
            self.conf = self.DEV_CONF
            self.project_version = 'a'
        elif project_version == 'a':
            self.conf = self.A_VERSION_CONF
        else:
            self.conf = self.B_VERSION_CONF
        self.virtualenv_bin = os.path.join(
            self.basedir,
            ".venv",
            "audb-" + self.project_version,
            "bin",
            "activate",
        )

    def update(self):
        self.puts("Checking if django project can run...")
        if not self.can_update:
            self.abort("Unable run django commands.")
        self.puts("Updating django project...")
        self.migrate()
        self.collectstatic()

    def migrate(self):
        self.puts("Migrating...")
        if not self.can_migrate:
            self.puts("No need to migrate.")
            return
        self.migrate_db()
        self.puts("Migration complete.")

    @property
    @with_env
    @from_basedir
    def can_update(self):
        with fab.hide("commands"), fab.settings(warn_only=True):
            result = self.cmd("python src/manage.py")
        return not result.failed

    @with_env
    @from_basedir
    def collectstatic(self):
        self.puts("Collecting static...")
        with fab.hide("commands"):
            self.cmd("yes yes | python src/manage.py collectstatic")
        self.puts("Collecting static complete.")

    @with_env
    @from_basedir
    def migrate_db(self):
        with fab.hide("commands"):
            self.cmd("python src/manage.py migrate")

    @with_env
    @from_basedir
    def can_migrate(self):
        with fab.hide("everything"), fab.settings(warn_only=True):
            cmd = r'python src/manage.py showmigrations -l 2>1 | grep "^\[ \]"'
            result = self.cmd(cmd)
        return not result.failed
