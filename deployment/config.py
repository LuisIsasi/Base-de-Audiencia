from fabric import api as fab, colors
from fabric.contrib.console import confirm


prod_roledefs = {
    'app': {
        'hosts': [
            'aud01.geprod.amc',
        ],
    },
    'job': {
        'hosts': [
            'aud-jobs01.geprod.amc',
        ],
    },
    'nginx': {
        'hosts': [
            'aud01.geprod.amc',
        ],
    },
    'system': {
        'hosts': [
            'aud01.geprod.amc',
        ],
    },
}


dev_roledefs = {
    'app': {
        'hosts': [
            'aud01.gedev.amc',
        ],
    },
    'job': {
        'hosts': [
            'aud-jobs01.gedev.amc',
        ],
    },
    'nginx': {
        'hosts': [
            'aud01.gedev.amc',
        ],
    },
    'system': {
        'hosts': [
            'aud01.gedev.amc',
        ],
    },
}


def setup_environment():
    """Configures the fabric environment for deployment.
    By default, things are assumed to be run on dev. This is done to make prod
    deployment a conscious action.
    In order to set prod, you must add the switch: --set prod
    """
    if 'repo_branch' not in fab.env:
        fab.env.repo_branch = 'master'
    fab.env.sudo_user = 'deploy'

    try:
        fab.env.prod
    except:
        fab.puts(colors.blue("{}".format(80 * '=')))
        fab.puts(colors.blue(" Running in dev environment."))
        fab.puts(colors.blue("{}\n".format(80 * '=')))
        fab.env.roledefs = dev_roledefs
        fab.env.prod = False
    else:
        question = colors.yellow("You are attempting to run commands on prod. Are you sure?")
        if confirm(question):
            fab.puts(colors.blue("{}".format(80 * '=')))
            fab.puts(colors.blue(" Running in prod environment."))
            fab.puts(colors.blue("{}\n".format(80 * '=')))
            fab.env.roledefs = prod_roledefs
        else:
            fab.abort(colors.red("Deployment to production cancelled."))
