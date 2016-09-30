# encoding: utf-8

from .linux import UnixFrontend


def get_instance(platform, conf):
    return this_class(platform, conf)


class BusyboxFrontend(UnixFrontend):

    def install_package(self, *package):
        self.execute('opkg-install {}'.format(' '.join(package)))

    def get_version(self, app):
        raise RuntimeError("Method 'get_versio'n is not available")

this_class = BusyboxFrontend
