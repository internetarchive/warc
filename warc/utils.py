"""
warc.utils
~~~~~~~~~~

This file is part of warc

:copyright: (c) 2012 Internet Archive
"""

from collections import MutableMapping, Mapping
from http.client import HTTPMessage
import email.parser
import sys
import re

SEP = re.compile("[;:=]")

class CaseInsensitiveDict(MutableMapping):
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
    def __init__(self, *args, **kwargs):
        self._d = {}
        self.update(dict(*args, **kwargs))

    def __setitem__(self, name, value):
        self._d[name.lower()] = value

    def __getitem__(self, name):
        return self._d[name.lower()]

    def __delitem__(self, name):
        del self._d[name.lower()]

    def __eq__(self, other):
        return isinstance(other, CaseInsensitiveDict) and other._d == self._d

    def __iter__(self):
        return iter(self._d)

    def __len__(self):
        return len(self._d)

class FilePart:
    """File interface over a part of file.

    Takes a file and length to read from the file and returns a file-object
    over that part of the file.
    """
    def __init__(self, fileobj, length):
        self.fileobj = fileobj
        self.length = length
        self.offset = 0
        self.buf = b''

    def read(self, size=-1):
        if size == -1:
            size = self.length

        if len(self.buf) >= size:
            content = self.buf[:size]
            self.buf = self.buf[size:]
        else:
            size = min(size, self.length - self.offset)
            content = self.buf + self.fileobj.read(size - len(self.buf))
            self.buf = b''
        self.offset += len(content)
        return content

    def _unread(self, content):
        self.buf = content + self.buf
        self.offset -= len(content)

    def readline(self, size=1024):
        chunks = []
        chunk = self.read(size)
        while chunk and b"\n" not in chunk:
            chunks.append(chunk)
            chunk = self.read(size)

        if b"\n" in chunk:
            index = chunk.index(b"\n")
            self._unread(chunk[index+1:])
            chunk = chunk[:index+1]
        chunks.append(chunk)
        return b"".join(chunks)

    def __iter__(self):
        line = self.readline()
        while line:
            yield line
            line = self.readline()
