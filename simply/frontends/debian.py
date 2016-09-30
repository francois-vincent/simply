# encoding: utf-8

from .. import utils
from .linux import UnixFrontend


def get_instance(platform, conf):
    return this_class(platform, conf)


class DebianFrontend(UnixFrontend):

    def install_package(self, *package):
        if self.package_installer_init:
            self.execute('apt-get update && apt-get upgrade -y')
            self.package_installer_init = False
        self.execute('apt-get install -y {}'.format(' '.join(package)))

    def get_version(self, app):
        output = self.execute('apt-cache policy {}'.format(app), user='root')
        try:
            return utils.extract_column(utils.filter_column(output, 0, startswith='Install'), 1, sep=':')[0]
        except IndexError:
            pass

this_class = DebianFrontend
