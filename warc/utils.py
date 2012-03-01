"""
warc
~~~~

This file is part of warc

:copyright: (c) 2012 Internet Archive
"""

from UserDict import DictMixin

class CaseInsensitiveDict(DictMixin):
    """Almost like a dictionary, but keys are case-insensitive.
    
        >>> d = CaseInsensitiveDict(foo=1, Bar=2)
        >>> d['foo']
        1
        >>> d['bar']
        2
        >>> d['Foo'] = 11
        >>> d['FOO']
        11
        >>> d.keys()
        ["foo", "bar"]
    """
    def __init__(self, mapping=None, **kwargs):
        self._d = {}
        self.update(mapping, **kwargs)
        
    def __setitem__(self, name, value):
        self._d[name.lower()] = value
    
    def __getitem__(self, name):
        return self._d[name.lower()]
        
    def __delitem__(self, name):
        del self._d[name.lower()]
        
    def __eq__(self, other):
        return isinstance(other, CaseInsensitiveDict) and other._d == self._d
        
    def keys(self):
        return self._d.keys()
