import os

from fabric import api as fab, colors

from .command import Command, from_basedir
from .util import slack


class Repo(Command):

    def __init__(self, branch=None, *args, **kwargs):
        super(Repo, self).__init__(*args, **kwargs)
        self.branch = fab.env.repo_branch or 'master'
        self.force_checkout = 'force_checkout' in fab.env and fab.env.force_checkout
        self.repo_name = os.path.basename(self.basedir)

    def update(self):
        self.puts("Updating repo {}...".format(self.repo_name))
        self.puts("Checking if update is allowed...")
        if not self.can_update:
            msg = [colors.red("Refusing to update repo.")]
            if not self.is_clean:
                msg.append("Branch is {}.".format(colors.red('dirty')))
            if not self.is_proper_branch:
                msg.append(
                    "Expected branch {}. Actual Branch: {}.".format(
                        colors.white(self.branch, bold=True),
                        colors.red(self.current_branch)
                    )
                )
            self.abort("\n".join(msg))

        self.puts("Pulling on {}...".format(self.branch))
        self.pull()
        self.puts("Finished updating repo.")

    @from_basedir
    def checkout(self):
        self.puts("Checking out branch: {}".format(self.branch))
        slack('Switching branch to {}'.format(self.branch))

        if self.is_clean:
            self.cmd('git checkout {}'.format(self.branch))
        else:
            self.abort("Unable to checkout unclean branch.")

    @from_basedir
    def pull(self):
        with fab.hide("commands"):
            self.cmd('git pull --ff-only')

    @property
    def can_update(self):
        return self.is_clean and self.is_proper_branch

    @property
    @from_basedir
    def current_branch(self):
        with fab.hide("everything"):
            result = self.cmd('git symbolic-ref -q HEAD')
        return result.split('/')[-1]

    @property
    @from_basedir
    def is_clean(self):
        with fab.hide("everything"), fab.settings(warn_only=True):
            result = self.cmd('git diff --no-ext-diff --quiet --ignore-submodules --exit-code')
        return not result.failed

    @property
    def is_proper_branch(self):
        if self.branch != self.current_branch:
            if not self.force_checkout:
                return False
            self.puts("Forcing a checkout...")
            self.checkout()
        return self.branch == self.current_branch
