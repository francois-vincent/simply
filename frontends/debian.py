# encoding: utf-8

import time

from .. import utils


def get_instance(platform, conf):
    if not DebianFrontend.instance:
        DebianFrontend.instance = DebianFrontend(platform, conf)
    return DebianFrontend.instance


class DebianFrontend(object):
    instance = None
    type = 'debian'

    def __init__(self, platform, conf):
        self.platform = platform
        self.execute = platform.execute

    def create_user(self, user, container, groups=(), home=None, shell=None):
        """ Create a user with optional groups, home and shell
        """
        cmd = 'useradd {}{}{}'.\
            format(user,
                   ' -d {}'.format(home) if home else '',
                   ' -s {}'.format(shell) if shell else '')
        self.execute(cmd, container)
        existing_groups = utils.extract_column(self.execute('cat /etc/group', container), 0, sep=':')
        for group in groups:
            if group not in existing_groups:
                self.execute('addgroup {}'.format(group), container)
            self.execute('usermod -a -G {} {}'.format(group, user), container)

    def path_set_user(self, path, user, container, group=None, recursive=False):
        cmd = 'chown{} {}{} {}'.format(' -R' if recursive else '', user, ':{}'.format(group) if group else '', path)
        return self.execute(cmd, container, status_only=True, raises=True)

    def set_permissions(self, path, perms, container, recursive=False):
        cmd = 'chmod{} {} {}'.format(' -R' if recursive else '', perms, path)
        return self.execute(cmd, container, status_only=True, raises=True)

    def get_version(self, app, container):
        output = self.execute('apt-cache policy {}'.format(app), container, user='root')
        try:
            return utils.extract_column(utils.filter_column(output, 0, startswith='Install'), 1, sep=':')[0]
        except IndexError:
            pass

    def wait_running_process(self, cmd, container, timeout=1):
        count, step = timeout, 0.2
        while count > 0:
            if cmd in utils.extract_column(self.execute('ps -A', container, user='root'), -1, 1):
                return True
            time.sleep(step)
            count -= step

    def get_processes(self, container, filter=None):
        processes = utils.extract_column(self.execute('ps -A', container, user='root'), -1, 1)
        if filter is None:
            return processes
        return [proc for proc in processes if filter in proc]


get_class = DebianFrontend
