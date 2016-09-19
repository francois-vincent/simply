# encoding: utf-8

from contextlib import contextmanager
import cStringIO
import os.path
import random
from subprocess import Popen, PIPE, call
import sys
import threading


# ======================= GENERAL UTILILITIES =======================

def extract_column(text, column, start=0, sep=None):
    """ Extracts columns from a formatted text
    :param text:
    :param column: the column number: from 0, -1 = last column
    :param start: the line number to start with (headers removal)
    :param sep: optional separator between words  (default is arbitrary number of blanks)
    :return: a list of words
    """
    lines = text.splitlines() if isinstance(text, basestring) else text
    if start:
        lines = lines[start:]
    values = []
    for line in lines:
        elts = line.split(sep) if sep else line.split()
        if elts and column < len(elts):
            values.append(elts[column].strip())
    return values


def filter_column(text, column, start=0, sep=None, **kwargs):
    """ Filters (like grep) lines of text according to a specified column and operator/value
    :param text: a string
    :param column: integer >=0
    :param sep: optional separator between words  (default is arbitrary number of blanks)
    :param kwargs: operator=value eg eq='exact match', contains='substring', startswith='prefix' etc...
    :return: a list of split lines
    """
    if len(kwargs) != 1:
        raise TypeError("Missing or too many keyword parameter in filter_column")
    op, value = kwargs.items()[0]
    if op in ('eq', 'equals'):
        op = '__eq__'
    elif op in ('contains', 'includes'):
        op = '__contains__'
    elif not op in ('startswith', 'endswith'):
        raise ValueError("Unknown filter_column operator: {}".format(op))
    lines = text.splitlines() if isinstance(text, basestring) else text
    if start:
        lines = lines[start:]
    values = []
    for line in lines:
        elts = line.split(sep) if sep else line.split()
        if elts and column < len(elts):
            elt = elts[column]
            if getattr(elt, op)(value):
                values.append(line.strip())
    return values


def random_id(len=16):
    return ''.join(random.choice('0123456789abcdefghijklmnopqrstuvwxyz') for _ in xrange(len))

# ======================= OS RELATED UTILITIES =======================

# this is explicitly borrowed from fabric
def _wrap_with(code):
    def inner(text, bold=False):
        c = code
        if bold:
            c = "1;%s" % c
        return "\033[%sm%s\033[0m" % (c, text)
    return inner

red = _wrap_with('31')
green = _wrap_with('32')
yellow = _wrap_with('33')
blue = _wrap_with('34')
magenta = _wrap_with('35')
cyan = _wrap_with('36')
white = _wrap_with('37')


@contextmanager
def cd(folder):
    old_folder = os.getcwd()
    yield os.chdir(folder)
    os.chdir(old_folder)


COMMAND_DEBUG = None
# COMMAND_DEBUG = 'Debug: '


class Command(object):
    """ Use this class if you want to wait and get shell command output
    """
    def __init__(self, cmd, show=COMMAND_DEBUG):
        self.show = show
        self.p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        self.out_buf = cStringIO.StringIO()
        self.err_buff = cStringIO.StringIO()
        t_out = threading.Thread(target=self.out_handler)
        t_err = threading.Thread(target=self.err_handler)
        t_out.start()
        t_err.start()
        self.p.wait()
        t_out.join()
        t_err.join()
        self.p.stdout.close()
        self.p.stderr.close()
        self.stdout = self.out_buf.getvalue()
        self.stderr = self.err_buff.getvalue()
        self.returncode = self.p.returncode

    def out_handler(self):
        for line in iter(self.p.stdout.readline, ''):
            if self.show is not None:
                sys.stdout.write(self.show + line)
            self.out_buf.write(line)

    def err_handler(self):
        for line in iter(self.p.stderr.readline, ''):
            if self.show is not None:
                sys.stderr.write(self.show + 'Error: ' + line)
            self.err_buff.write(line)

    def stdout_column(self, column, start=0):
        return extract_column(self.stdout, column, start)


def command(cmd, raises=False):
    """ Use this function if you only want the return code.
        You can't retrieve stdout nor stderr and it never raises
    """
    ret = call(cmd, shell=True)
    if ret and raises:
        raise RuntimeError("Error while executing<{}>".format(cmd))
    return ret


def command_input(cmd, datain, raises=False):
    """ Use this if you want to send data to stdin
    """
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    p.communicate(datain)
    if p.returncode and raises:
        raise RuntimeError("Error while executing<{}>".format(cmd))
    return p.returncode


class ConfAttrDict(dict):
    """
    A configuration attribute dictionary with a context manager that allows to push and pull items,
    eg for configuration overriding.
    """
    class Remove_:
        pass

    def __getattr__(self, item):
        if item in self:
            return self[item]
        raise AttributeError("{} attribute not found: {}".format(self.__class__.__name__, item))

    def update(self, E=None, **F):
        dict.update(self, E, **F)
        return self

    def __iadd__(self, other):
        return self.update(other)

    def __add__(self, other):
        return ConfAttrDict(self).update(other)

    def __isub__(self, other):
        for k in other:
            if k in self:
                del self[k]
        return self

    def __sub__(self, other):
        return ConfAttrDict(self).__isub__(other)

    def push(self, **kwargs):
        if not hasattr(self, '__item_stack'):
            self.__item_stack = []
            self.__missing_stack = []
        self.__item_stack.append({k: self[k] for k in kwargs if k in self})
        kkwargs = kwargs
        for k in kwargs:
            if kwargs[k] is ConfAttrDict.Remove_:
                if kkwargs is kwargs:
                    kkwargs = dict(kwargs)
                del kkwargs[k]
                if k in self:
                    del self[k]
        self.__missing_stack.append([k for k in kkwargs if k not in self])
        return self.update(kkwargs)

    def pull(self):
        for k in self.__missing_stack.pop():
            del self[k]
        return self.update(self.__item_stack.pop())

    def __call__(self, **kwargs):
        return self.push(**kwargs)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.pull()


def read_configuration(conf_file):
    if not os.path.isfile(conf_file):
        raise RuntimeError("File %s not found" % conf_file)
    conf = ConfAttrDict()
    with open(conf_file, "rb") as f:
        exec(compile(f.read(), conf_file, 'exec'), {}, conf)
    return conf
