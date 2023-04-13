from functools import wraps

from fabric import api as fab, colors

from deployment import config
from deployment.host import AppHost, JobHost
from deployment.util import slack

config.setup_environment()


def prod_only(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not fab.env.prod:
            fab.abort(colors.red("This command is only applicable in the prod environment."))
        return f(*args, **kwargs)
    return wrapper


@fab.task
@fab.roles("nginx")
@prod_only
def toggle_live():
    host = AppHost()
    host.discover_audb_versions()
    fab.execute(switch_live, to=host.stage)


@fab.task
@fab.roles("nginx")
@prod_only
def switch_live(to="a"):
    if to not in ['a', 'b']:
        fab.abort(colors.red("Unknown version: " + to))
    fab.puts(colors.blue("Switching live to: " + colors.blue(to, bold=True)))
    slack('Toggling live to {}'.format(to))

    host = AppHost()
    host.switch_live(to)

    host.discover_audb_versions()
    if host.live != to:
        fab.abort(colors.red("Live switch failed."))
    fab.puts(colors.blue("Live switch complete."))


@fab.task
def can_deploy_apps(to='stage'):
    if to not in ['stage', 'live']:
        fab.abort(colors.red("Unknown target: " + to))
    host = AppHost()
    host.discover_audb_versions(silent=True)
    if to == 'live':
        return host.can_deploy_to_live()
    return host.can_deploy_to_stage()


@fab.task
def can_deploy_jobs(to='stage'):
    if to not in ['stage', 'live']:
        fab.abort(colors.red("Unknown target: " + to))
    host = JobHost()
    host.discover_audb_versions(silent=True)
    if to == 'live':
        return host.can_deploy_to_live()
    return host.can_deploy_to_stage()


@fab.task
def can_deploy_system():
    host = AppHost()
    return host.can_deploy_to_system()


@fab.task
def status():
    fab.puts("So what'cha, what'cha, what'cha want? (what'cha want?)")
    fab.puts("I get so funny with my money that you flaunt.")
    fab.puts("I said, \"Where'd you get your information from\", huh?")
    fab.puts("You think that you can front when revelation comes?")


@fab.task
def deploy(to='stage'):
    if to not in ['stage', 'live']:
        fab.abort(colors.red("Unknown target: " + to))

    fab.puts(colors.blue("Verifying deployment is possible..."))
    slack('Starting deploy to {}'.format(to))

    for host in fab.env.roledefs['app']['hosts']:
        if not fab.execute(can_deploy_apps, hosts=[host], to=to):
            fab.abort(colors.red("Unable to deploy to host: " + host))

    for host in fab.env.roledefs['job']['hosts']:
        if not fab.execute(can_deploy_jobs, hosts=[host], to=to):
            fab.abort(colors.red("Unable to deploy to host: " + host))

    for host in fab.env.roledefs['system']['hosts']:
        if not fab.execute(can_deploy_system, hosts=[host]):
            fab.abort(colors.red("Unable to deploy to host: " + host))

    fab.puts(colors.blue("Deploying to {} on the app servers...".format(to)))
    fab.execute(deploy_apps, to=to)

    fab.puts(colors.blue("\nDeploying to {} on the job servers...".format(to)))
    fab.execute(deploy_jobs, to=to)

    fab.puts(colors.blue("\nDeploying to system on all servers..."))
    fab.execute(deploy_system)

    fab.puts(colors.blue("Deploy complete"))
    slack('Finished deploy to {}'.format(to))


@fab.task
@fab.roles('system')
def deploy_system():
    slack('Deploying to system on all servers')
    host = AppHost()
    host.deploy_to_system()


@fab.task
@fab.roles('app')
def deploy_apps(to='stage'):
    if to not in ['stage', 'live']:
        fab.abort("Unknown target: " + to)

    slack('Deploying to {} on the app servers'.format(to))
    host = AppHost()
    __deploy(host, to)


@fab.task
@fab.roles('job')
def deploy_jobs(to='stage'):
    if to not in ['stage', 'live']:
        fab.abort(colors.red("Unknown target: " + to))

    slack('Deploying to {} on the job servers'.format(to))
    host = JobHost()
    __deploy(host, to)


def __deploy(host, to):
    host.discover_audb_versions()

    if to == 'live':
        host.deploy_to_live()
    else:
        host.deploy_to_stage()
