# encoding: utf-8

from .platform import Backend


class DockerManager(Backend):
    buildable = True
    runnable = True
    class_name = 'image'
    host_name = 'container'

    def __init__(self):
        pass

