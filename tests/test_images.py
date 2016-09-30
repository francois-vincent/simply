# encoding: utf-8

from simply.platform import platform_setup
from simply.utils import ConfAttrDict

std_python2_path = '/usr/local/lib/python2.7'
std_python3_path = '/usr/local/lib/python3.'


def test_debian8():
    conf = ConfAttrDict(
        backend='docker',
        frontend='debian',
        image='debian8',
    )
    with platform_setup(conf) as platform:
        assert 'Python 2.7' in platform.execute('python -V', stdout_only=False).stderr
        assert std_python2_path in platform.execute('pip -V')
        assert platform.execute('pip install pytest')
        assert std_python2_path in platform.execute('py.test --version', stdout_only=False).stderr


def test_conda2():
    conf = ConfAttrDict(
        backend='docker',
        frontend='busybox',
        image='conda2',
    )
    with platform_setup(conf) as platform:
        assert 'Python 2.7' in platform.execute('python -V', stdout_only=False).stderr
        python_path = '/root/miniconda/lib/python2.7'
        assert python_path in platform.execute('pip -V')
        assert platform.execute('pip install pytest')
        assert python_path in platform.execute('py.test --version', stdout_only=False).stderr


def test_conda3():
    conf = ConfAttrDict(
        backend='docker',
        frontend='busybox',
        image='conda3',
    )
    with platform_setup(conf) as platform:
        assert 'Python 3.4' in platform.execute('python -V', stdout_only=False).stderr
        python_path = '/root/miniconda3/lib/python3.4'
        assert python_path in platform.execute('pip -V')
        assert platform.execute('pip install pytest')
        assert python_path in platform.execute('py.test --version', stdout_only=False).stderr


def test_phusion():
    conf = ConfAttrDict(
        backend='docker',
        frontend='debian',
        image='phusion',
    )
    with platform_setup(conf) as platform:
        assert 'Python 2.7' in platform.execute('python -V', stdout_only=False).stderr
        assert std_python2_path in platform.execute('pip2 -V')
        assert platform.execute('pip2 install pytest')
        assert std_python2_path in platform.execute('py.test --version', stdout_only=False).stderr
        assert 'Python 3.' in platform.execute('python3 -V')
        assert std_python3_path in platform.execute('pip3 -V')
        assert platform.execute('pip3 install pytest')
        assert std_python3_path in platform.execute('py.test --version', stdout_only=False).stderr
