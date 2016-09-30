# encoding: utf-8

from contextlib import contextmanager
import time

import pytest
import requests

from simply.platform import factory
from simply.utils import ConfAttrDict


@contextmanager
def platform_setup(conf):
    platform = factory(conf)
    platform.setup('all_containers')
    yield platform
    platform.reset()


@pytest.mark.parametrize("image", ['conda2', 'conda3', 'debian8'])
def test_matrix(image):
    print('test on image <{}>'.format(image))


@pytest.mark.parametrize("interprter,http_server", [('python2', 'SimpleHTTPServer'), ('python3', 'http.server')])
def test_python_server(interprter, http_server):
    conf = ConfAttrDict(
        backend='docker',
        frontend='debian',
        image='phusion',
    )
    with platform_setup(conf) as platform:
        platform.execute("{} -m {} 8000".format(interprter, http_server), daemon=True)
        time.sleep(0.1)
        req = requests.get('http://{}:8000'.format(platform.get_container_ip()), timeout=1)
        assert req.status_code == 200
        assert 'Directory listing for' in req.text
