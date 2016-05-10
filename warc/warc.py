"""
warc.warc
~~~~~~~~~

Python library to work with WARC files.

:copyright: (c) 2012 Internet Archive
"""

import gzip
import builtins
import datetime
import uuid
import re
import io
import hashlib

from .utils import CaseInsensitiveDict, FilePart, get_http_headers


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
    TODO:
        List of attributes needed to make WARCHeaders look like ARC files

        * url
        * ip_address
        * date (date of archival)
        * content_type
        * result_code (response code)
        * checksum
        * location
        * offset (offset from beginning of file to recrod)
        * filename (name of arc file)
        * length (length of the n/w doc in bytes)

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
        super().__init__(headers)
        if defaults:
            self.init_defaults()
        self.version = "WARC/%s" % self.get('warc-version', '1.0')

    def init_defaults(self):
        """Initializes important headers to default values,
        if not already specified.

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

    def write_to(self, f):
        """Writes this header to a file, in the format specified by WARC.
        """
        f.write(self.version.encode() + b"\r\n")
        for name, value in self.items():
            name = name.title()
            # Use standard forms for commonly used patterns
            name = (name.replace("Warc-", "WARC-")
                    .replace("-Ip-", "-IP-")
                    .replace("-Id", "-ID")
                    .replace("-Uri", "-URI"))
            f.write(str(name).encode())
            f.write(b": ")
            f.write(str(value).encode())
            f.write(b"\r\n")

        # Header ends with an extra CRLF
        f.write(b"\r\n")

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
        f = io.BytesIO()
        self.write_to(f)
        return str(f.getvalue(), 'utf-8')

    def __repr__(self):
        return "<WARCHeader: type=%r, record_id=%r>" % (self.type, self.record_id)


class WARCRecord(object):
    """The WARCRecord object represents a WARC Record.
    """
    def __init__(self, header=None, payload=None,  headers={}, defaults=True):
        """Creates a new WARC record.

           @param payload must be of type 'bytes' or FilePart
        """

        if header is None and defaults is True:
            headers.setdefault("WARC-Type", "response")

        self.header = header or WARCHeader(headers, defaults=True)

        if defaults is True and 'Content-Length' not in self.header:
            if payload:
                self.header['Content-Length'] = len(payload)
            else:
                self.header['Content-Length'] = "0"

        if defaults is True and 'WARC-Payload-Digest' not in self.header:
            self.header['WARC-Payload-Digest'] = self._compute_digest(payload)

        if isinstance(payload, bytes):
            payload = io.BytesIO(payload)

        self.payload = payload
        self._content = None

        self._custom_cases()

    def _custom_cases(self):
        # TODO: this need to be done using other pattern, but first we need
        # tests
        if self.version == '0.18':
            self._custom_0_18()

    def _custom_0_18(self):
        if not self.type == 'response':
            return

        if not self['content-type'].startswith('application/http'):
            return

        headers = get_http_headers(self.payload)
        self.header['http_headers'] = headers

    def _compute_digest(self, payload):
        return "sha1:" + hashlib.sha1(payload).hexdigest()

    def write_to(self, f):
        self.header.write_to(f)
        f.write(self.payload.read())
        f.write(b"\r\n")
        f.write(b"\r\n")
        f.flush()

    @property
    def type(self):
        """Record type"""
        return self.header.type

    @property
    def url(self):
        """The value of the WARC-Target-URI header if the record is of type "response"."""
        return self.header.get('WARC-Target-URI')

    @property
    def ip_address(self):
        """The IP address of the host contacted to retrieve the content of this record.

        This value is available from the WARC-IP-Address header."""
        return self.header.get('WARC-IP-Address')

    @property
    def date(self):
        """UTC timestamp of the record."""
        return self.header.get("WARC-Date")

    @property
    def checksum(self):
        return self.header.get('WARC-Payload-Digest')

    @property
    def version(self):
        return self.header['warc-version']

    @property
    def offset(self):
        """Offset of this record in the warc file from which this record is read.
        """
        pass

    def __getitem__(self, name):
        try:
            return self.header[name]
        except KeyError:
            if name == "content_type":
                return self.content.type
            elif name in self.content:
                return self.content[name]

    def __setitem__(self, name, value):
        self.header[name] = value

    def __contains__(self, name):
        return name in self.header

    def __str__(self):
        f = io.BytesIO()
        self.write_to(f)
        return str(f.getvalue())

    def __repr__(self):
        return "<WARCRecord: type=%r record_id=%s>" % (self.type,
                                                       self['WARC-Record-ID'])

    @staticmethod
    def from_response(response):
        """Creates a WARCRecord from given response object.

        This must be called before reading the response. The response can be
        read after this method is called.

        :param response: An instance of :class:`requests.models.Response`.
        """
        # Get the httplib.HTTPResponse object
        http_response = response.raw._original_response

        # HTTP status line, headers as string
        status_line = "HTTP/1.1 %d %s" % (http_response.status,
                                          http_response.reason)
        headers = str(http_response.msg)

        # Read raw response data out of request
        stream = io.BytesIO()
        stream.write(status_line.encode())
        stream.write(b'\r\n')
        stream.write(http_response.msg.as_bytes())
        stream.write(b'\r\n')
        for chunk in response.iter_content(1024):
            stream.write(chunk)

        payload = stream.getvalue()

        headers = {
            "WARC-Type": "response",
            "WARC-Target-URI": response.request.url
        }
        return WARCRecord(payload=payload, headers=headers)


class WARCFile:
    def __init__(self, filename=None, mode=None, fileobj=None, compress=None):
        if fileobj is None:
            fileobj = builtins.open(filename, mode or "rb")
            mode = fileobj.mode
        # initiaize compress based on filename, if not already specified
        if compress is None and filename and filename.endswith(".gz"):
            compress = True

        if compress:
            fileobj = gzip.open(fileobj.name, mode)

        self.fileobj = fileobj
        self._reader = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __iter__(self):
        return iter(self.reader)

    @property
    def reader(self):
        if self._reader is None:
            self._reader = WARCReader(self.fileobj)
        return self._reader

    def write_record(self, warc_record):
        """Adds a warc record to this WARC file.
        """
        warc_record.write_to(self.fileobj)

    def read_record(self):
        """Reads a warc record from this WARC file."""
        return self.reader.read_record()

    def close(self):
        self.fileobj.close()

    def browse(self):
        """Utility to browse through the records in the warc file.

        This returns an iterator over (record, offset, size) for each record in
        the file. If the file is gzip compressed, the offset and size will
        corresponds to the compressed file.

        The payload of each record is limited to 1MB to keep memory consumption
        under control.
        """
        offset = 0
        for record in self.reader:
            # Just read the first 1MB of the payload.
            # This will make sure memory consuption is under control and it
            # is possible to look at the first MB of the payload, which is
            # typically sufficient to read http headers in the payload.
            record.payload = io.BytesIO(record.payload.read(1024*1024))
            self.reader.finish_reading_current_record()
            next_offset = self.tell()
            yield record, offset, next_offset-offset
            offset = next_offset

    def tell(self):
        """Returns the file offset.
        """
        return self.fileobj.tell()


class WARCReader:
    RE_VERSION = re.compile("WARC/(\d+.\d+)\r\n")
    RE_HEADER = re.compile(r"([a-zA-Z_\-]+): *(.*)\r\n")
    SUPPORTED_VERSIONS = ["1.0", "0.18"]

    def __init__(self, fileobj):
        self.fileobj = fileobj
        self.current_payload = None

    def read_header(self, fileobj):
        version_line = fileobj.readline().decode("utf-8")
        if not version_line:
            return None

        m = self.RE_VERSION.match(version_line)
        if not m:
            raise IOError("Bad version line: %r" % version_line)
        version = m.group(1)
        if version not in self.SUPPORTED_VERSIONS:
            raise IOError("Unsupported WARC version: %s" % version)

        headers = {
            'warc-version': version,
        }
        while True:
            line = fileobj.readline().decode("utf-8")
            if line == "\r\n":  # end of headers
                break
            m = self.RE_HEADER.match(line)
            if not m:
                raise IOError("Bad header line: %r" % line)
            name, value = m.groups()
            headers[name] = value
        return WARCHeader(headers)

    def expect(self, fileobj, expected_line, message=None):
        line = fileobj.readline().decode("utf-8")
        if line != expected_line:
            message = message or "Expected %r, found %r" % (expected_line, line)
            raise IOError(message)

    def finish_reading_current_record(self):
        # consume the footer from the previous record
        if self.current_payload:
            # consume all data from the current_payload before
            # moving to next record
            self.current_payload.read()
            self.expect(self.current_payload.fileobj, "\r\n")
            if self.current_payload.length:
                self.expect(self.current_payload.fileobj, "\r\n")
            self.current_payload = None

    def read_record(self):
        self.finish_reading_current_record()
        fileobj = self.fileobj

        header = self.read_header(fileobj)
        if header is None:
            return None

        self.current_payload = FilePart(fileobj, header.content_length)
        record = WARCRecord(header, self.current_payload, defaults=False)
        return record

    def _read_payload(self, fileobj, content_length):
        size = 0
        if content_length <= 0:
            yield b''
            raise StopIteration

        while size < content_length:
            chunk_size = min(1024, content_length-size)
            chunk = fileobj.read(chunk_size)
            size += chunk_size
            yield chunk

    def __iter__(self):
        record = self.read_record()
        while record is not None:
            yield record
            record = self.read_record()
