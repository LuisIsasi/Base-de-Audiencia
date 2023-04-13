import os
from functools import wraps
from fabric import api as fab, colors


def from_basedir(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        with self.cd(self.basedir):
            return f(self, *args, **kwargs)
    return wrapper


class Command(object):
    def __init__(self, basedir=None, remote=False):
        if basedir is not None:
            self.basedir = basedir
        else:
            self.basedir = os.path.dirname(fab.env.real_fabfile)

        if remote:
            self.cd = fab.cd
            self.cmd = self.remote
        else:
            self.cd = fab.lcd
            self.cmd = self.local

    @classmethod
    def remote(cls, *args, **kwargs):
        if 'user' not in kwargs:
            kwargs['user'] = fab.env.sudo_user

        return fab.sudo(*args, **kwargs)

    @classmethod
    def local(cls, *args, **kwargs):
        if 'capture' not in kwargs:
            kwargs['capture'] = True
        return fab.local(*args, **kwargs)

    def puts(self, msg):
        fab.puts(colors.blue(msg), flush=True)

    def abort(self, msg):
        fab.abort(colors.red(msg))
