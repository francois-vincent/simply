# encoding: utf-8

from .. import utils
from .docker_cmds import (get_images, get_containers, container_stop, container_delete,
                          image_delete, image_delete_and_containers, docker_build, docker_pull,
                          docker_run, docker_exec)


class DockerBackend(object):

    def init_backend(self, conf):
        self.container = conf.get('container') or self.image + '_' + utils.random_id()
        self.parameters = conf.get('parameters')
        self.image_spec = conf.get('image_spec', '')
        return self

    def setup_backend(self):
        return self

    def setup(self, reset=None):
        """
        1- ensures images are created, otherwise, creates them
        2- ensures containers are created and started otherwise creates and/or starts them
        """
        self.build_image(reset)
        self.run_container()
        return self

    def reset(self, reset='rm_image'):
        """ Resets a platform
        :param reset: 'uproot': remove platform images and any dependant container
                      'rm_image': remove platform images and containers
                      'rm_container': remove and stop platform containers
                      'stop': stop platform containers
        """
        if not reset:
            return self
        if reset == 'uproot':
            self.image_delete(uproot=True)
            return self
        if reset in ('stop', 'rm_container', 'rm_image'):
            self.container_stop()
        if reset in ('rm_container', 'rm_image'):
            self.container_delete()
        if reset == 'rm_image':
            self.image_delete()
        return self

    def build_image(self, reset=None):
        self.reset(reset)
        if self.image not in self.get_real_images():
            if self.image_spec == '.pull':
                print(utils.yellow("Pull image {}".format(self.image)))
                docker_pull(self.image)
            else:
                print(utils.yellow("Build image {}".format(self.image)))
                if '\n' in self.image_spec:
                    docker_build(self.image_spec, self.image)
                else:
                    docker_build(self.image)
        return self

    def image_exist(self):
        return [self.image] == self.get_real_images()

    def run_container(self, reset=None):
        self.reset(reset)
        if self.container in self.get_real_containers():
            return self
        self.container_delete()
        docker_run(self.image, self.container, self.container, self.parameters)
        return self

    def get_real_images(self):
        return get_images(self.image)

    def get_real_containers(self, all=False):
        return get_containers(self.container, all=all)

    def image_delete(self, uproot=False):
        func = image_delete_and_containers if uproot else image_delete
        for image in self.get_real_images():
            print(utils.red("Delete image {}".format(image)))
            func(image)
        return self

    def container_stop(self):
        for container in self.get_real_containers():
            print(utils.yellow("Stop container {}".format(container)))
            container_stop(container)
        return self

    def container_delete(self):
        for container in self.get_real_containers(True):
            print(utils.yellow("Delete container {}".format(container)))
            container_delete(container)
        return self

    def execute(self, cmd, **kwargs):
        return docker_exec(cmd, self.container, self.user, **kwargs)


this_class = DockerBackend
