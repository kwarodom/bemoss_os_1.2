
import sys

_ver = sys.version_info
is_py2 = (_ver[0] == 2)
is_py3 = (_ver[0] == 3)


if is_py2:  # pragma: no cover
    from urllib import (quote, unquote, quote_plus, unquote_plus, urlencode,
                        getproxies, proxy_bypass)
    from urlparse import urlparse, urlunparse, urljoin, urlsplit, urldefrag
    from urllib2 import parse_http_list
    import cookielib
    from Cookie import Morsel
    from StringIO import StringIO
    from httplib import IncompleteRead

    builtin_str = str
    bytes = str
    str = unicode
    basestring = basestring
    numeric_types = (int, long, float)
    execfile = execfile


elif is_py3:  # pragma: no cover
    from urllib.parse import (urlparse, urlunparse, urljoin, urlsplit,
                              urlencode, quote, unquote, quote_plus,
                              unquote_plus, urldefrag)
    from urllib.request import parse_http_list, getproxies, proxy_bypass
    from http import cookiejar as cookielib
    from http.cookies import Morsel
    from io import StringIO
    from http.client import IncompleteRead

    builtin_str = str
    str = str
    bytes = bytes
    basestring = (str, bytes)
    numeric_types = (int, float)

    def execfile(filename, globals=None, locals=None):
        if globals is None:
            globals = sys._getframe(1).f_globals
        if locals is None:
            locals = sys._getframe(1).f_locals
        with open(filename, "r") as fh:
            exec(fh.read()+"\n", globals, locals)


def python_2_unicode_compatible(cls):
    """
    A decorator that defines __unicode__ and __str__ methods under Python
    2. Under Python 3 it does nothing.

    To support Python 2 and 3 with a single code base, define a __str__
    method returning unicode text and apply this decorator to the class.

    The implementation comes from django.utils.encoding.
    """
    if not is_py3:  # pragma: no cover
        cls.__unicode__ = cls.__str__
        cls.__str__ = lambda self: self.__unicode__().encode('utf-8')
    return cls
