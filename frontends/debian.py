# encoding: utf-8

from .common_unix import UnixFrontend


def get_instance(platform, conf):
    return DebianFrontend(platform, conf)


class DebianFrontend(UnixFrontend):

    def install_package(self, package):
        if self.package_installer_init:
            self.execute('apt-get update && apt-get upgrade -y')
            self.package_installer_init = False
        self.execute('apt-get install -y {}'.format(package))

this_class = DebianFrontend
