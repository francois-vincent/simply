# encoding: utf-8

import pytest

from .. import ROOTDIR
from ..utils import cd, extract_column, filter_column, Command, command, command_input, run_sequence


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
