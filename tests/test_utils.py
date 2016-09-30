# encoding: utf-8

import os
import pytest

from simply import ROOTDIR
from simply.utils import (cd, extract_column, filter_column, Command, command, command_input,
                          ConfAttrDict, read_configuration)


def test_extract_column():
    assert extract_column('', 0, 0) == []
    text = """a1 a2 a3 a4
       b1 b2 b3 b4
       c1 c2 c3     c4
       d1  d2 d3  d4
    """
    assert extract_column(text, 0, 0) == ['a1', 'b1', 'c1', 'd1']
    assert extract_column(text, -1, 0) == ['a4', 'b4', 'c4', 'd4']
    assert extract_column(text, 0, 1) == ['b1', 'c1', 'd1']
    assert extract_column(text, 1, 1) == ['b2', 'c2', 'd2']


def test_filter_column():
    with pytest.raises(TypeError):
        filter_column('', 0)
    with pytest.raises(ValueError):
        filter_column('', 0, toto='')
    text = """toto titi bob
       tototo xtitito blob
       aaaa bbbb job
    """
    assert filter_column(text, 0, eq='toto') == ['toto titi bob']
    assert filter_column(text, 0, startswith='toto') == ['toto titi bob', 'tototo xtitito blob']
    assert filter_column(text, 1, contains='titi') == ['toto titi bob', 'tototo xtitito blob']
    assert filter_column(text, 2, endswith='ob') == ['toto titi bob', 'tototo xtitito blob', 'aaaa bbbb job']


def test_Command(capsys):
    with cd(ROOTDIR):
        com = Command('pwd')
    assert com.returncode == 0
    assert com.stdout.strip() == ROOTDIR
    assert com.stderr == ''
    out, err = capsys.readouterr()
    assert (out, err) == ('', '')
    com = Command('fancycommand')
    assert com.returncode > 0
    assert com.stdout == ''
    assert com.stderr.strip() == '/bin/sh: 1: fancycommand: not found'
    out, err = capsys.readouterr()
    assert (out, err) == ('', '')


def test_Command_show(capsys):
    prefix = 'TEST: '
    with cd(ROOTDIR):
        com = Command('pwd', show=prefix)
    assert com.returncode == 0
    assert com.stdout.strip() == ROOTDIR
    assert com.stderr == ''
    out, err = capsys.readouterr()
    assert (out.strip(), err) == (prefix + ROOTDIR, '')
    com = Command('fancycommand', show=prefix)
    assert com.returncode > 0
    assert com.stdout == ''
    assert com.stderr.strip() == '/bin/sh: 1: fancycommand: not found'
    out, err = capsys.readouterr()
    assert (out, err.strip()) == ('', prefix + 'Error: /bin/sh: 1: fancycommand: not found')


def test_command(capsys):
    # you can't retrieve stdout nor stdin
    assert command('pwd') == 0
    # surprisingly, capsys does not capture stdout nor stderr
    out, err = capsys.readouterr()
    assert (out, err) == ('', '')
    assert command('fancycommand') > 0
    out, err = capsys.readouterr()
    assert (out, err) == ('', '')


def test_command_input(capsys):
    assert command_input('cat -', 'qsjqkjjf') == 0
    out, err = capsys.readouterr()
    assert (out, err) == ('', '')


def test_atr_dict():
    cad = ConfAttrDict(a=1, b=2, c=3)
    assert len(cad) == 3
    assert cad.a == 1
    # default behaviour is to raise on missing attribute
    with pytest.raises(AttributeError):
        cad.d
    # but it can be overridden to return any default value
    cad._raises = None
    assert cad.d is None
    cad._raises = ConfAttrDict.__raises__

    with cad(a=10, d=11):
        assert len(cad) == 4
        assert cad.a == 10
        assert cad.d == 11
    assert len(cad) == 3
    assert cad.a == 1
    with pytest.raises(AttributeError):
        cad.d

    with cad(a=ConfAttrDict.__void__, d=ConfAttrDict.__void__):
        assert len(cad) == 2
        with pytest.raises(AttributeError):
            cad.a
        with pytest.raises(AttributeError):
            cad.d
    assert len(cad) == 3
    assert cad.a == 1
    with pytest.raises(AttributeError):
        cad.d

    cad += dict(d=4)
    assert len(cad) == 4
    assert cad.d == 4
    cad -= ('a', 'd')
    assert len(cad) == 2
    with pytest.raises(AttributeError):
        cad.a
    with pytest.raises(AttributeError):
        cad.d

    cad2 = cad + dict(a=1)
    assert len(cad) == 2
    assert len(cad2) == 3

    cad3 = cad2 - dict(a=1)
    assert len(cad2) == 3
    assert len(cad3) == 2
    assert cad == cad3


def test_python_conf():
    conf = """
titi = 1 + 1
toto = TEST_ENVIRON
"""
    os.environ['TEST_ENVIRON'] = 'python'
    x, y = read_configuration(conf, '.py')
    assert y == 'inline'
    assert x.titi == 2
    assert x.toto == os.environ['TEST_ENVIRON']


def test_json_conf():
    conf = """
{
  "titi": 2,
  "toto": "json"
}
"""
    x, y = read_configuration(conf, '.json')
    assert y == 'inline'
    assert x.titi == 2
    assert x.toto == 'json'


def test_yaml_conf():
    conf = """
titi: 2
toto: yaml
"""
    x, y = read_configuration(conf, '.yaml')
    assert y == 'inline'
    assert x.titi == 2
    assert x.toto == 'yaml'
