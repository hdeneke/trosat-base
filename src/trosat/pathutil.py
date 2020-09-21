import string
import os
import re
import pathlib
from sys import maxsize as maxint
from collections import ChainMap

# import cached_property
while True:
    # first, try to import cached_property from functools
    # (available only in Python 3.8 and above)
    try:
        from functools import cached_property
        break
    except ImportError:
        pass
    # second, try to import cached_property from cached_property package
    try:
        from cached_property import cached_property
        break
    except ImportError:
        pass
    # finally, define to be identical to property
    cached_property = property
    break

_regex_var =  re.compile('\$(\{)?(\w+)(?(1)\})',re.ASCII)

def expandvars(s, env=os.environ):
    '''
    Expand environment variables in string.
    '''
    return _regex_var.sub(lambda m: env[m[2]] if m[2] in env else m[0], s)


class PathFormatter(string.Formatter):
    
    # custom conversion characters
    conv_map = {
        'l' : str.lower,         # lower-case conversion char
        'u' : str.upper,         # upper-case conversion char
        't' : str.title,         # title-case conversion char
        'c' : str.capitalize     # capitalization conversion char
    }

    def __init__(self, fmt, expandvars=True, expanduser=True, env_defaults=None):
        '''
        Constructor which takes fmt string as argument.
        '''
        self._fmt        = fmt
        self._expandvars = expandvars
        self._expanduser = expanduser
        self._env        = ChainMap(os.environ,env_defaults)  \
                           if env_defaults else os.environ
        return super().__init__()

    def __call__(self, *args, **kwargs):
        '''
        Make PathFormatter instances callable by calling vformat method
        '''
        return self.vformat(args, kwargs)

    def convert_field(self, val, c):
        '''
        Use custom conversion characters for formatting fields in
        lower/upper/... case.
        '''
        return self.conv_map[c](val) if c in self.conv_map else super().convert_field(val, c)

    def get_value(self, key, args, kwargs):
        '''
        get value
        '''
        if key=='ENV' and self._expandvars:
            retval = self._env
        else:
            retval = super().get_value(key, args, kwargs)
        return retval
    
    def format(self, *args, **kwargs):
        '''
        Use _fmt attribute for formatting and return Path instance.
        '''
        return self.vformat(args, kwargs)
    
    def vformat(self, args, kwargs):
        '''
        Use _fmt attribute for formatting and return Path instance.
        '''
        fmt = self._fmt
        if self._expandvars:
            fmt = expandvars(fmt, self._env)
        if self._expanduser:
            fmt = os.path.expanduser(fmt)
        return pathlib.Path(super().vformat(fmt, args, kwargs))


class PathMatcher(object):
    '''
    Matcher object for matching paths against a regular expression.

    Parameters
    ---------- 
    pattern : str
         The regular expression used for matching.
    flags : int
         Flags for the regular expression.
    pmap : callable or None
         A mapping function to be applied to the path, e.g. os.path.dirname or
         os.path.basename. If None, the path is used unmodified for matching.

    Examples
    ---------- 
    >>> import os, pathutils, pathlib
    >>> # create testfile
    >>> p = pathlib.Path('./msg3-sevi-20130512T120000Z-test.dat')
    >>> p.write_text('x')
    >>> # create PathMatcher
    >>> kwargs = {
    >>>     'pathmap' :  os.path.basename,
    >>>     'groupmap' : {'time': lambda s: datetime.datetime.strptime(s,'%Y%m%d%H%MZ')}
    >>> }
    >>> pm = pathutil.PathMatcher('^(?P<sat>msg\d)-sevi-(?P<time>\d{8}T\d{6}Z)', **kwargs)
    >>> # match path, returning a PathMatch object
    >>> m = pm.match(p)
    >>> # access fields by name
    >>> print(m['sat'],m['time'])
    >>> # m is Path-like object, so can be passed to os file functions
    >>> os.unlink(m)
    '''

    def __init__(self, pattern, flags=0, fullmatch=True, pathmap=None, groupindex=None, groupmap=None):
        '''
        '''
        self._pattern = re.compile(pattern, flags)
        self._pathmap    = pathmap
        self._groupindex    = groupindex
        self._groupmap    = groupmap
        self._matchfun  = self.fullmatch if fullmatch else self.match
        return

    def __call__(self, *args, **kwargs):
        return self._matchfun(*args, **kwargs)

    def match(self, p, **kwargs):
        '''
        Match the path
        '''
        _ = str(p) if self._pathmap is None else self._pathmap(str(p))
        m = self._pattern.match(_, **kwargs)
        return PathMatch(m, p, self._groupindex, self._groupmap) if m else None

    def fullmatch(self, p, **kwargs):
        _ = str(p) if self._pathmap is None else self._pathmap(str(p))
        m = self._pattern.fullmatch(_, **kwargs)
        return PathMatch(m, p, self._groupindex, self._groupmap) if m else None

class PathMatch(object):

    # define fixed set of slots to limit memory usage
    __slots__ = [ '_match', '_path', '_groupindex', '_groupmap' ]

    def __init__(self, match, path, groupindex=None, groupmap=None):
        self._match = match
        self._path = path
        self._groupindex  = ChainMap(groupindex.copy(), self._match.re.groupindex) if groupindex else self._match.re.groupindex
        if groupmap:
            self._groupmap = {}
            for k, v in groupmap.items():
                if type(k)==str and k in self._groupindex:
                    self._groupmap[self._groupindex[k]] = v
                else:
                    self._groupmap[k] = v
        else:
            self._groupmap = None
        return

    def __fspath__(self):
        '''
        Function to implement PathLike protocol, see https://docs.python.org/3/library/os.html#os.PathLike
        '''
        return self._path

    def __getattr__(self, k):
        '''
        Access named group matches as attribute
        '''
        try:
            return self.group(k)
        except IndexError as e:
            raise AttributeError(*e.args)

    def __getitem__(self, k):
        '''
        Access matches by item lookup
        '''
        return self.group(k)

    def group(self, k):
        k = self._groupindex[k] if type(k)==str and k in self._groupindex else k
        g = self._match.group(k)
        if self._groupmap and k in self._groupmap:
            return self._groupmap[k](g)
        else:
            return g

    def groups(self):
        return tuple(self.group(i) for i in range(self.nr_groups()+1))

    def nr_groups(self):
        return self._match.re.groups

    def groupdict(self):
        return { k:self.group(k) for k in self._groupindex.keys() }

            


