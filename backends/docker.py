# encoding: utf-8

from ..platform import Backend
from ..utils import command


def get_backend_class():
    return DockerBackend


class DockerBackend(Backend):
    blueprint_name = 'image'
    host_name = 'container'

    def __init__(self, conf, platform=None):
        self.images = conf['images']
        self.hosts = conf['hosts']
        self.platform = platform

    def get_hosts(self, spec=None):
        if spec == 'ip':
            return self
        return self.hosts

    def run_command(self, cmd, host, input_data=None, raises=False):
        pass

    def test_command(self, cmd, host, shell=None):
        docker_cmd = 'docker exec -i {} {}'.format(self.hosts[host], '{} "{}"'.format(shell, cmd) if shell else cmd)
        return not command(docker_cmd)

    def standard_setup(self):
        self.build_images()
        self.setup_network()
        self.run_containers('rm_container')
        return self.connect_network()
