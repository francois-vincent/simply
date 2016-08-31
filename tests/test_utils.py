# encoding: utf-8

import pytest

from .. import ROOTDIR
from ..utils import (cd, extract_column, filter_column, Command, command, command_input, run_sequence,
                     collapse_self, collapse_op, set_method, set_methods_from_conf)


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


def test_sequencer():
    class Toto(object):
        x = []
        def a(self):
            self.x.append('a')
        def b(self, p):
            self.x.append(('b', p))
        def c(self, p1, p2):
            self.x.append(('c', p1, p2))
        def d(self, *args):
            self.x.append(('d', args))
        def e(self, p, k=None):
            self.x.append(('e', p, k))
        def f(self, *args, **kwargs):
            self.x.append(('f', args, kwargs))

    toto = Toto()
    run_sequence(toto, 'a', ('b', 1), ('c', (1, 2)), ('d', (1, 2)),
                 ('e', (1, 2)), ('e', (1, ), {'k': 3}), ('f', (1, ), {'x': 2}))
    toto.x = ['a', ('b', 1), ('c', 1, 2), ('d', (1, 2)), ('e', 1, 2), ('e', 1, 3), ('f', (1,), {'x': 2})]


def test_decorators():
    class Test(object):
        hosts = {'h1': 'container1', 'h2': 'container2'}
        @collapse_op('dict')
        def get_hosts(self, host, a, b=None):
            return self.hosts[host]
        @collapse_self
        def get_self(self, host, *args, **kwargs):
            pass
        @collapse_op('all')
        def get_true(self, host):
            return True
        @collapse_op('append')
        def get_list(self, host):
            return self.hosts[host]

    t = Test()
    assert t.get_hosts('', host='h1') == Test.hosts['h1']
    assert t.get_hosts('') == Test.hosts
    assert t.get_self() is t
    assert t.get_self(host='h1') is t
    assert t.get_true()
    assert t.get_true(host='h1')
    assert set(t.get_list()) == set(Test.hosts.values())
    assert t.get_list(host='h1') == Test.hosts['h1']


def test_set_method():
    class Test(object):
        pass

    def toto(self, param):
        return param

    t = Test()
    with pytest.raises(AttributeError):
        t.toto(12)
    set_method(Test, toto)
    assert hasattr(Test, 'toto')
    assert hasattr(t, 'toto')
    assert t.toto(12) == 12


def test_set_methods_from_conf():
    class Test(object):
        hosts = {'h1': 'container1', 'h2': 'container2'}

    def toto(self, host, param):
        return param

    conf = dict(toto=toto)
    set_methods_from_conf(Test, conf)
    assert Test().toto(12) == {'h1': 12, 'h2': 12}
