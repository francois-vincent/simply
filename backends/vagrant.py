# encoding: utf-8

from platform import Backend
from utils import command


def get_backend_class():
    return DockerBackend


class DockerBackend(Backend):
    blueprint_name = ''
    host_name = 'VM'

    def __init__(self, conf, platform=None):
        self.images = conf.images
        self.hosts = conf.hosts
        self.platform = platform

    def get_hosts(self, spec=None):
        if spec == 'ip':
            return self
        return self.hosts

    def run_command(self, cmd, host, input_data=None, raises=False):
        pass

    def test_command(self, cmd, host, shell=None):
        pass

    def standard_setup(self):
        return self

