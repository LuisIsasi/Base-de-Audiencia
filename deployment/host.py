from fabric import api as fab, colors

from deployment.django import Django
from deployment.repo import Repo


class Host(object):

    def __init__(self):
        self.live = None
        self.stage = None
        self.dev = not fab.env.prod
        if self.dev:  # There is no stage/live distinction with dev currently.
            self.project_versions = {
                'a': '/data/local/apps/audb-a',
                'b': '/data/local/apps/audb-a',
            }
        else:
            self.project_versions = {
                'a': '/data/local/apps/audb-a',
                'b': '/data/local/apps/audb-b',
            }

        self.system_path = '/data/shared/audb-system'

    def discover_audb_versions(self, silent=False):
        self.live = self.get_live_version()
        if self.live == 'a':
            self.stage = 'b'
        else:
            self.stage = 'a'
        if not silent:
            msg = (
                colors.blue("Live version is ") + colors.blue(self.live, bold=True) + "." +
                colors.blue(" Stage version is ") + colors.blue(self.stage, bold=True) + "."
            )
            fab.puts(msg, flush=True)

    def get_live_path(self):
        try:
            return self.project_versions[self.live]
        except KeyError:
            fab.abort("Unable to determine path. " + colors.red("Live is not set correctly."))

    def get_stage_path(self):
        try:
            return self.project_versions[self.stage]
        except KeyError:
            fab.abort("Unable to determine path. " + colors.red("Stage is not set correctly."))

    def get_system_path(self):
        return self.system_path

    def get_live_version(self):
        with fab.hide("commands"):
            live_version = fab.sudo("get-audb-version").lower()
        if live_version not in ['a', 'b', '?']:
            fab.abort(colors.red("Unexpected return value for audb version: '{}'.".format(live_version)))
        if live_version == '?':
            fab.abort(colors.red("Unable to determine live version."))
        return live_version

    def can_deploy_to_live(self):
        path = self.get_live_path()
        repo = Repo(basedir=path, remote=True)
        django = Django(dev=self.dev, project_version=self.live, basedir=path, remote=True)
        return self._can_deploy(repo, django)

    def can_deploy_to_stage(self):
        path = self.get_stage_path()
        repo = Repo(basedir=path, remote=True)
        django = Django(dev=self.dev, project_version=self.stage, basedir=path, remote=True)
        return self._can_deploy(repo, django)

    def can_deploy_to_system(self):
        path = self.get_system_path()
        repo = Repo(basedir=path, remote=True)
        repo_good = repo.can_update
        if not repo_good:
            fab.puts(colors.red("Repository is dirty."))
        return repo_good

    def deploy_to_live(self):
        path = self.get_live_path()
        project_version = self.live

        repo = Repo(basedir=path, remote=True)
        repo.update()

        dj_project = Django(dev=self.dev, project_version=project_version, basedir=path, remote=True)
        dj_project.update()

    def deploy_to_stage(self):
        path = self.get_stage_path()
        project_version = self.stage

        repo = Repo(basedir=path, remote=True)
        repo.update()

        dj_project = Django(dev=self.dev, project_version=project_version, basedir=path, remote=True)
        dj_project.update()

    def deploy_to_system(self):
        path = self.get_system_path()
        repo = Repo(basedir=path, remote=True)
        repo.update()

    def puts(self, msg):
        fab.puts(colors.blue(msg), flush=True)

    def _can_deploy(self, repo, django):
        repo_good = repo.can_update
        django_good = django.can_update
        if not repo_good:
            fab.puts(colors.red("Repository is dirty."))
        if not django_good:
            fab.puts(colors.red("Unable to run django commands."))
        return repo_good and django_good

    def _validate_project_version(self, version):
        versions = self.project_versions.keys()
        if version not in versions:
            fab.abort("\n".join([
                colors.red("Unknown project version."),
                "Valid choices are: " + ", ".join(versions)
            ]))


class AppHost(Host):

    def switch_live(self, to):
        self._validate_project_version(to)
        with fab.hide("commands"):
            fab.sudo("swap-audb " + to)

    def deploy_to_live(self):
        super(AppHost, self).deploy_to_live()
        self.__bounce_server(self.live)

    def deploy_to_stage(self):
        super(AppHost, self).deploy_to_stage()
        self.__bounce_server(self.stage)

    def __bounce_server(self, version):
        self._validate_project_version(version)

        project = self.project_versions[version]
        self.puts("Bouncing app server...")
        with fab.hide("commands"), fab.cd(project):
            fab.sudo("touch uwsgi.touch")


class JobHost(Host):

    def __init__(self, *args, **kwargs):
        super(JobHost, self).__init__(*args, **kwargs)
        if self.dev:
            self.worker_process = {
                'a': 'celery',
                'b': 'celery',
            }
            self.beat_process = {
                'a': 'celerybeat',
                'b': 'celerybeat',
            }
        else:
            self.worker_process = {
                'a': 'celery-a',
                'b': 'celery-b',
            }
            self.beat_process = {
                'a': 'celerybeat-a',
                'b': 'celerybeat-b',
            }

    def deploy_to_live(self):
        super(JobHost, self).deploy_to_live()
        self.puts("Bouncing celery workers...")
        with fab.hide("running"):
            fab.sudo("sudo supervisorctl restart " + self.worker_process[self.live])

        self.puts("Bouncing celerybeat...")
        with fab.hide("running"):
            fab.sudo("sudo supervisorctl restart " + self.beat_process[self.live])

    def deploy_to_stage(self):
        super(JobHost, self).deploy_to_stage()

        self.puts("Bouncing celery workers...")
        with fab.hide("running"):
            fab.sudo("sudo supervisorctl restart " + self.worker_process[self.stage])

        self.puts("Stopping celerybeat...")
        with fab.hide("running"):
            fab.sudo("sudo supervisorctl stop " + self.beat_process[self.stage])
