"""
warc
~~~~

Python library to work with WARC files.

:copyright: (c) 2012 by Anand Chitipothu.
"""

import __builtin__
import datetime
import uuid
import logging
import re
from cStringIO import StringIO
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

class WARCHeader(CaseInsensitiveDict):
    """The WARC Header object represents the headers of a WARC record.

    It provides dictionary like interface for accessing the headers.    
    
    The following mandatory fields are accessible also as attributes.
    
        * h.record_id == h['WARC-Record-ID']
        * h.content_length == int(h['Content-Length'])
        * h.date == h['WARC-Date']
        * h.type == h['WARC-Type']
        
    :params headers: dictionary of headers. 
    :params defaults: If True, important headers like WARC-Record-ID, 
                      WARC-Date, Content-Type and Content-Length are
                      initialized to automatically if not already present.
    """
    
    CONTENT_TYPES = dict(warcinfo='application/warc-fields',
                        response='application/http; msgtype=response',
                        request='application/http; msgtype=request',
                        metadata='application/warc-fields')
                            
    KNOWN_HEADERS = {
        "type": "WARC-Type",
        "date": "WARC-Date",
        "record_id": "WARC-Record-ID",
        "ip_address": "WARC-IP-Address",
        "target_uri": "WARC-Target-URI",
        "warcinfo_id": "WARC-Warcinfo-ID",
        "request_uri": "WARC-Request-URI",
        "content_type": "Content-Type",
        "content_length": "Content-Length"
    }
                            
    def __init__(self, headers, defaults=False):
        self.version = "WARC/1.0"
        CaseInsensitiveDict.__init__(self, headers)
        if defaults:
            self.init_defaults()
        
    def init_defaults(self):
        """Initializes important headers to default values, if not already specified.
        
        The WARC-Record-ID header is set to a newly generated UUID.
        The WARC-Date header is set to the current datetime.
        The Content-Type is set based on the WARC-Type header.
        The Content-Length is initialized to 0.
        """
        if "WARC-Record-ID" not in self:
            self['WARC-Record-ID'] = "<urn:uuid:%s>" % uuid.uuid1()
        if "WARC-Date" not in self:
            self['WARC-Date'] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        if "Content-Type" not in self:
            self['Content-Type'] = WARCHeader.CONTENT_TYPES.get(self.type, "application/octet-stream")
        self.setdefault("Content-Length", "0")
                        
    def write_to(self, f):
        """Writes this header to a file, in the format specified by WARC.
        """
        f.write(self.version + "\r\n")
        for name, value in self.items():
            name = name.title()
            # Use standard forms for commonly used patterns
            name = name.replace("Warc-", "WARC-").replace("-Ip-", "-IP-").replace("-Id", "-ID").replace("-Uri", "-URI")
            f.write(name)
            f.write(": ")
            f.write(value)
            f.write("\r\n")
        
        # Header ends with an extra CRLF
        f.write("\r\n")

    @property
    def content_length(self):
        """The Content-Length header as int."""
        return int(self['Content-Length'])
        
    @property
    def type(self): 
        """The value of WARC-Type header."""
        return self['WARC-Type']
        
    @property
    def record_id(self):
        """The value of WARC-Record-ID header."""
        return self['WARC-Record-ID']
        
    @property
    def date(self):
        """The value of WARC-Date header."""
        return self['WARC-Date']
    
    def __str__(self):
        f = StringIO()
        self.write_to(f)
        return f.getvalue()
        
    def __repr__(self):
        return "<WARCHeader: type=%r, record_id=%r>" % (self.type, self.record_id)

class WARCRecord:
    """The WARCRecord object represents a WARC Record.
    """
    def __init__(self, header=None, payload=None,  headers={}):
        """Creates a new WARC record. 
        """
        self.header = header or WARCHeader(headers, defaults=True)
        self.payload = payload
        if payload:
            self.header['Content-Length'] = str(len(payload))
        else:
            self.header['Content-Length'] = "0"
        
    def write_to(self, f):
        self.header.write_to(f)
        f.write(self.payload)
        f.write("\r\n")
        f.write("\r\n")
        
    def __getitem__(self, name):
        return self.header[name]

    def __setitem__(self, name, value):
        self.header[name] = value
        
    def __contains__(self, name):
        return name in self.header
        
    def __str__(self):
        f = StringIO()
        self.write_to(f)
        return f.getvalue()
    
    def __repr__(self):
        return "<WARCRecord: type=%r record_id=%s>" % (self['type'], self['record_id'])
        
    @staticmethod
    def from_response(response):
        """Creates a WARCRecord from given response object.

        This must be called before reading the response. The response can be 
        read after this method is called.
        
        :param response: An instance of :class:`requests.models.Response`.
        """
        # Get the httplib.HTTPResponse object
        http_response = response.raw._original_response
        
        # HTTP status line, headers and body as strings
        status_line = "HTTP/1.1 %d %s" % (http_response.status, http_response.reason)
        headers = str(http_response.msg)
        body = http_response.read()

        # Monkey-patch the response object so that it is possible to read from it later.
        response.raw._fp = StringIO(body)

        # Build the payload to create warc file.
        payload = status_line + "\r\n" + headers + "\r\n" + body
        
        headers = {
            "WARC-Type": "response",
            "WARC-Target-URI": response.request.full_url.encode('utf-8')
        }
        return WARCRecord(payload=payload, headers=headers)

class WARCFile:
    def __init__(self, filename=None, mode=None, fileobj=None):
        if fileobj is None:
            fileobj = __builtin__.open(filename, mode or "rb")
        self.fileobj = fileobj
    
    def write(self, warc_record):
        """Adds a warc record to this WARC file.
        """
        warc_record.write_to(self.fileobj)
        
    def read(self):
        """Reads a warc record from this WARC file."""
        reader = WARCReader(self.fileobj)
        return reader.read_record()
        
    def __iter__(self):
        reader = WARCReader(self.fileobj)
        return iter(reader)
        
    def close(self):
        self.fileobj.close()
        
def open(filename, mode="rb"):
    """Shorthand for WARCFile(filename, mode).
    """
    return WARCFile(filename, mode)

class WARCReader:
    RE_VERSION = re.compile("WARC/(\d+.\d+)\r\n")
    RE_HEADER = re.compile(r"([a-zA-Z_\-]+): *(.*)\r\n")
    SUPPORTED_VERSIONS = ["1.0"]
    
    def __init__(self, fileobj):
        self.fileobj = fileobj
    
    def read_header(self):
        version_line = self.fileobj.readline()
        if not version_line:
            return None
            
        m = self.RE_VERSION.match(version_line)
        if not m:
            raise IOError("Bad version line: %r" % version_line)
        version = m.group(1)
        if version not in self.SUPPORTED_VERSIONS:
            raise IOError("Not supported WARC version: %s" % version)
            
        headers = {}
        while True:
            line = self.fileobj.readline()
            if line == "\r\n": # end of headers
                break
            m = self.RE_HEADER.match(line)
            if not m:
                raise IOError("Bad header line: %r" % line)
            name, value = m.groups()
            headers[name] = value
        return WARCHeader(headers)
        
    def expect(self, expected_line, message=None):
        line = self.fileobj.readline()
        if line != expected_line:
            message = message or "Expected %r, found %r" % (expected_line, line)
            raise IOError(message)

    def read_record(self):
        header = self.read_header()
        if header is None:
            return None
        payload = self.fileobj.read(header.content_length)
        record = WARCRecord(header, payload)
        self.expect("\r\n")
        self.expect("\r\n")
        return record

    def __iter__(self):
        record = self.read_record()
        while record is not None:
            yield record
            record = self.read_record()
