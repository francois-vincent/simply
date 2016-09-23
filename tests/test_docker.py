# encoding: utf-8

import os.path

from .. import ROOTDIR
from ..backends import docker, get_class
from ..utils import ConfAttrDict


def test_version():
    version = docker.docker_version()
    assert len(version.split('.')) == 3


def test_build():
    docker.image_delete_and_containers('scratch')
    try:
        assert docker.docker_build('scratch')
        assert docker.get_images('scratch') == ['scratch']
    finally:
        docker.image_delete('scratch')


def test_build_inline():
    inline = """
FROM scratch
CMD ["/bin/cat"]
"""
    docker.image_delete_and_containers('scratch')
    try:
        assert docker.docker_build(inline, tag='scratch')
        assert docker.get_images('scratch') == ['scratch']
    finally:
        docker.image_delete('scratch')


def test_container_delete():
    docker.image_delete_and_containers('scratch')
    try:
        # performs a test of docker_run by the way, so I removed test_run()
        assert docker.docker_build('scratch')
        assert docker.docker_run('scratch', parameters='-v /bin:/bin')
        assert len(docker.get_containers(image='scratch')) == 1
        # delete by image name
        assert docker.container_delete(image='scratch')
        assert len(docker.get_containers(image='scratch')) == 0
        assert docker.docker_run('scratch', parameters='-v /bin:/bin')
        # delete by container name
        containers = docker.get_containers(image='scratch')
        assert docker.container_delete(*containers)
        assert len(docker.get_containers(image='scratch')) == 0
    finally:
        docker.image_delete_and_containers('scratch')


def test_exec():
    docker.container_delete(image='busybox')
    try:
        assert docker.docker_run('busybox', 'busybox', parameters='-i', cmd='/bin/cat')
        res = docker.docker_exec('ls', 'busybox').split('\n')
        assert len(res) > 9
        assert 'bin' in res
        assert 'etc' in res
    finally:
        docker.container_delete(image='busybox')


def test_path_exists():
    docker.container_delete(image='busybox')
    try:
        assert docker.docker_run('busybox', 'busybox', parameters='-i', cmd='/bin/cat')
        assert docker.path_exists('/bin', 'busybox')
    finally:
        docker.container_delete(image='busybox')


def test_get_data():
    docker.container_delete(image='busybox')
    try:
        assert docker.docker_run('busybox', 'busybox', parameters='-i', cmd='/bin/cat')
        res = docker.get_data('/etc/passwd', 'busybox').split('\n')
        assert 'root:x:0:0:root:/root:/bin/sh' in res
    finally:
        docker.container_delete(image='busybox')


def test_put_file():
    docker.container_delete(image='busybox')
    try:
        assert docker.docker_run('busybox', 'busybox', parameters='-i', cmd='/bin/cat')
        file = os.path.join(ROOTDIR, '__init__.py')
        assert docker.put_file(file, '/', 'busybox')
        with open(file, 'r') as f:
            content = f.read()
        assert content == docker.get_data('/__init__.py', 'busybox')
    finally:
        docker.container_delete(image='busybox')


def test_put_data():
    docker.container_delete(image='busybox')
    try:
        assert docker.docker_run('busybox', 'busybox', parameters='-i', cmd='/bin/cat')
        file = os.path.join(ROOTDIR, '__init__.py')
        with open(file, 'r') as f:
            content = f.read()
        assert docker.put_data(content, '/__init__.py', 'busybox')
        assert content == docker.get_data('/__init__.py', 'busybox')
    finally:
        docker.container_delete(image='busybox')

# Test DockerBackend


def test_docker_import():
    conf = ConfAttrDict(
        backend='docker'
    )
    assert get_class(conf) is docker.this_class


def test_docker_conf():
    conf = ConfAttrDict()
    db = docker.this_class()
    db.image = 'busybox'
    assert db.init_backend(conf)
    assert db.parameters is None
    assert db.container.startswith(db.image)
    conf = ConfAttrDict(
        container='busybox',
        parameters='-v /bin:/bin'
    )
    db = docker.this_class()
    db.image = 'busybox'
    assert db.init_backend(conf)
    assert db.container == conf.container
    assert db.parameters == conf.parameters


def test_docker_pull():
    conf = ConfAttrDict(
        image_spec='.pull'
    )
    db = docker.this_class()
    db.image = 'busybox'
    assert db.init_backend(conf)
    assert db.build_image('uproot')
    assert db.image_exist()


def test_docker_build():
    conf = ConfAttrDict()
    db = docker.this_class()
    db.image = 'scratch'
    assert db.init_backend(conf)
    assert db.build_image('uproot')
    assert db.image_exist()


def test_docker_build_inline():
    conf = ConfAttrDict(
        image_spec="""
FROM scratch
CMD ["/bin/cat"]
"""
    )
    db = docker.this_class()
    db.image = 'scratch'
    assert db.init_backend(conf)
    assert db.build_image('uproot')
    assert db.image_exist()
