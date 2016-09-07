# encoding: utf-8

from contextlib import contextmanager
import cStringIO
import os.path
import re
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


def run_sequence(self, *args):
    """ run a sequence of methods with optional parameters from an object
    :param self: an object
    :param args: a sequence of:
       - string: call string()
       - tuple or list of:
          - (string, object): call string(object)
          - (string, tuple): call string(*tuple)
          - (string, tuple, dict): call string(*tuple, **dict)
    """
    for i, arg in enumerate(args):
        if isinstance(arg, basestring):
            getattr(self, arg)()
        elif len(arg) is 2:
            param = arg[1]
            if isinstance(param, tuple):
                getattr(self, arg[0])(*param)
            else:
                getattr(self, arg[0])(param)
        elif len(arg) is 3:
            getattr(self, arg[0])(*(arg[1]), **(arg[2]))
        else:
            raise RuntimeError('Bad argument at position {}: {}'.format(i, arg))
    return self


def set_method(cls, func, name=None, deco=None):
    setattr(cls, func.__name__ if name is None else name, func if deco is None else deco(func))


def collapse_op(op):
    """ Decorator to automatically execute a method on a specific host or all platform hosts,
        collecting return values in a dict or a list, or just testing them.
        The decorated method must have its first argument a host specifier (string).
        Usage: if the wrapper method is called with host='host' parameter, the wrapped
        method will be called once with this host.
        If the wrapper method is called with no host= parameter, the wrapped method will
        be called once per host of the platform. The wrapped method will then return a
        value depending of the op parameter.
        :param op:
        - dict:  a dictionary {host: value, ...} of the return values for each host.
        - extend or append: a concatenated list of return values, use 'extend' if
          the wrapped method returns a sequence, otherwise use 'append'.
        - and: a boolean, execution on multiple hosts stops as soon as the wrapped
          method returns False (good to check path or process exists on all hosts).
        - any: a boolean, execution on multiple hosts stops as soon as the wrapped
          method returns True (good to check missing path or process on all hosts).
    """
    op_values = ('dict', 'extend', 'append', 'and', 'any')
    def wrapper(meth):
        def wrapped(self, *args, **kwargs):
            host = kwargs.pop('host', None)
            if host:
                return meth(self, host, *args, **kwargs)
            elif op == 'dict':
                return {host: meth(self, host, *args, **kwargs) for host in self.hosts}
            elif op in ('extend', 'append'):
                ret = []
                for host in self.hosts:
                    getattr(ret, op)(meth(self, host, *args, **kwargs))
                return ret
            elif op == 'and':
                return all(meth(self, host, *args, **kwargs) for host in self.hosts)
            elif op == 'any':
                return any(meth(self, host, *args, **kwargs) for host in self.hosts)
            else:
                raise ValueError("Parameter op must be one of {}".format(op_values))
        return wrapped
    return wrapper


def collapse_self(meth):
    """ Like collapse_op, except that it always returns self
    """
    def wrapper(self, *args, **kwargs):
        host = kwargs.pop('host', None)
        if host:
            meth(self, host, *args, **kwargs)
        else:
            for host in self.hosts:
                meth(self, host, *args, **kwargs)
        return self
    return wrapper


def set_methods_from_conf(cls, conf):
    import utils
    regex = re.compile(r".*?\[deco:(\w+)\]")
    for k, v in conf.items():
        if hasattr(v, '__call__'):
            deco = collapse_op('dict')
            if getattr(v, '__doc__', None):
                deco_spec = regex.findall(v.__doc__)
                if deco_spec:
                    deco = getattr(utils, deco_spec[0])
            set_method(cls, v, k, deco)


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
    try:
        yield os.chdir(folder)
    finally:
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


def read_configuration(conf_file):
    if not os.path.isfile(conf_file):
        raise RuntimeError("File %s not found" % conf_file)
    conf = {}
    with open(conf_file, "rb") as f:
        exec(compile(f.read(), conf_file, 'exec'), {}, conf)
    return conf
