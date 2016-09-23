# encoding: utf-8

from contextlib import contextmanager
import cStringIO
import os
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


class ConfAttrDict(dict):
    """
    A configuration attribute dictionary with a context manager that allows to push and pull items,
    eg for configuration overriding.
    """
    class __void__: pass
    class __raises__: pass
    _raises = __raises__

    def __getattr__(self, item):
        if item in self:
            return self[item]
        if self._raises is ConfAttrDict.__raises__:
            raise AttributeError("{} attribute not found: {}".format(self.__class__.__name__, item))
        return self._raises

    def copy(self):
        return ConfAttrDict(self)

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

    def _push(self, **kwargs):
        if not hasattr(self, '__item_stack'):
            self.__item_stack = []
            self.__missing_stack = []
        self.__item_stack.append({k: self[k] for k in kwargs if k in self})
        kkwargs = kwargs
        for k in kwargs:
            if kwargs[k] is ConfAttrDict.__void__:
                if kkwargs is kwargs:
                    kkwargs = dict(kwargs)
                del kkwargs[k]
                if k in self:
                    del self[k]
        self.__missing_stack.append([k for k in kkwargs if k not in self])
        return self.update(kkwargs)

    def _pull(self):
        for k in self.__missing_stack.pop():
            del self[k]
        return self.update(self.__item_stack.pop())

    def __call__(self, **kwargs):
        return self._push(**kwargs)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._pull()


def random_id(len=10):
    return ''.join(random.choice('0123456789abcdefghijklmnopqrstuvwxyz') for _ in xrange(len))


def mixin_factory(name, base, *mixins):
    return type(name, (base,) + mixins, {})


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
        raise RuntimeError("Error while executing <{}>".format(cmd))
    return ret


def command_input(cmd, datain, raises=False):
    """ Use this if you want to send data to stdin
    """
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    p.communicate(datain)
    if p.returncode and raises:
        raise RuntimeError("Error while executing <{}>".format(cmd))
    return p.returncode


def find_file(file, path):
    """ returns the first file path found, in the specified path(es).
    :param file: an absolute file path or a file name.
    :param path: None or string or list, used only if file path is not absolute.
           if None or empty string, search in current directory.
           if '...', search recursively in current directory and its parents up to but not including '/'.
           if string, must be an absolute path to search for file.
           if list of strings, search in each specified path (can be '.', '..' or '...')
    :return: the first file path found
    """
    def check_path(file, path):
        if path == '...':
            path = os.getcwd()
            while path != '/':
                f = os.path.join(path, file)
                if os.path.isfile(f):
                    return f, True
                path = os.path.dirname(path)
            return file, False
        else:
            f = os.path.join(path, file)
            return f, os.path.isfile(f)

    if os.path.isabs(file):
        return file
    path = path or os.getcwd()
    if isinstance(path, basestring):
        file, is_file = check_path(file, path)
        if is_file:
            return file
        raise RuntimeError("File {} not found".format(file))
    else:
        for p in path:
            f, is_file = check_path(file, p)
            if is_file:
                return f
        raise RuntimeError("File {} not found in {}".format(file, path))


def read_configuration(file, path=None):
    """ read configuration from file or string
    :param file: a file name or an inline configuration string
    :param path: None or sting or list of string.
           if '.py' or '.yaml' or '.json', file is interpreted as an inline configuration string,
           if string or list of strings, specifies search path(es) for file (current directory if path is None)
    :return: a tuple (ConfAttrDict, config file path)
    """
    if path in ('.py', '.yaml', '.json'):
        data = file
        file, ext = 'inline', path
    else:
        _, ext = os.path.splitext(file)
        file = find_file(file, path)
        with open(file, 'r') as f:
            data = f.read()
    if ext == '.py':
        conf = ConfAttrDict()
        exec(compile(data, file, 'exec'), dict(os.environ), conf)
    elif ext in ('.yml', '.yaml'):
        import yaml
        conf = ConfAttrDict(yaml.load(data))
    elif ext == '.json':
        try:
            import simplejson as json
        except ImportError:
            import json
        conf = ConfAttrDict(json.loads(data))
    else:
        raise TypeError("Unknown file format %s" % file)
    return conf, file
