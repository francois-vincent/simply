# encoding: utf-8

import time

from .. import utils


class UnixFrontend(object):
    user = None

    def init_frontend(self, conf):
        self.package_installer_init = True
        self.effective_user = self.user or 'root'

    def setup_frontend(self):
        pass

    def create_user(self, user, groups=(), home=None, shell=None):
        """ Create a user with optional groups, home and shell
        """
        cmd = 'useradd {}{}{}'.\
            format(user,
                   ' -d {}'.format(home) if home else '',
                   ' -s {}'.format(shell) if shell else '')
        self.execute(cmd)
        existing_groups = utils.extract_column(self.execute('cat /etc/group'), 0, sep=':')
        for group in groups:
            if group not in existing_groups:
                self.execute('addgroup {}'.format(group))
            self.execute('usermod -a -G {} {}'.format(group, user))

    def path_set_user(self, path, user,  group=None, recursive=False):
        cmd = 'chown{} {}{} {}'.format(' -R' if recursive else '', user, ':{}'.format(group) if group else '', path)
        return self.execute(cmd, status_only=True, raises=True)

    def set_permissions(self, path, perms, recursive=False):
        cmd = 'chmod{} {} {}'.format(' -R' if recursive else '', perms, path)
        return self.execute(cmd, status_only=True, raises=True)

    def wait_running_process(self, cmd, timeout=1):
        count, step = timeout, 0.2
        while count > 0:
            if cmd in utils.extract_column(self.execute('ps -A', user='root'), -1, 1):
                return True
            time.sleep(step)
            count -= step

    def get_processes(self, filter=None):
        processes = utils.extract_column(self.execute('ps -A', user='root'), -1, 1)
        if filter is None:
            return processes
        return [proc for proc in processes if filter in proc]
