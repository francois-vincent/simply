# encoding: utf-8

import pytest

from ..platform import Platform, Backend


def test_platform_factory():
    hosts = {'h1': 'host1', 'h2': 'host2'}
    conf = dict(platforms={'test': {'backend': 'docker',
                                    'hosts': hosts,
                                    'images': hosts,
                                    }})
    p = Platform.factory(conf)
    assert len(p) == 1
    p = p[0]
    assert p.name == 'test'
    assert p.effective_user == 'root'
    assert p.hosts == hosts
