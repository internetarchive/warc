"""
Provides support for ARC v1 files.

:copyright: (c) 2012 Internet Archive
"""

import builtins
import datetime
import os
import re
import io
import warnings
import gzip

from .utils import CaseInsensitiveDict, status_code


ARC1_HEADER_RE = re.compile(('(?P<url>\S*)\s(?P<ip_address>\S*)\s(?P<date>\S*)'
                             '\s(?P<content_type>\S*)\s(?P<length>\S*)'))

ARC2_HEADER_RE = re.compile(('(?P<url>\S*)\s(?P<ip_address>\S*)\s(?P<date>\S*)'
                             '\s(?P<content_type>\S*)\s(?P<result_code>\S*)'
                             '\s(?P<checksum>\S*)\s(?P<location>\S*)'
                             '\s(?P<offset>\S*)\s(?P<filename>\S*)'
                             '\s(?P<length>\S*)'))


class ARCHeader(CaseInsensitiveDict):
    """
    Holds fields from an ARC V1 or V2 header.
    V1 header fields are

        * url
        * ip_address
        * date
        * content_type
        * length (length of the n/w doc in bytes)

    V2 header fields are

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
    def __init__(self, url="",  ip_address="",  date="",
                 content_type="", result_code="",  checksum="",
                 location="",  offset="",  filename="",  length=0,
                 version=2):

        if isinstance(date, datetime.datetime):
            date = date.strftime("%Y%m%d%H%M%S")
        else:
            try:
                datetime.datetime.strptime(date, "%Y%m%d%H%M%S")
            except ValueError:
                raise ValueError("Couldn't parse the date '%s' in file "
                                 "header" % date)

        self.version = version
        super().__init__({
            'url': url,
            'ip_address': ip_address,
            'date': date,
            'content_type': content_type,
            'result_code': result_code,
            'checksum': checksum,
            'location': location,
            'offset': offset,
            'filename': filename,
            'length': int(length),
        })

    def write_to(self, f, version=None):
        """
        Writes out the arc header to the file like object `f`.

        If the version field is 1, it writes out an arc v1 header,
        otherwise (and this is default), it outputs a v2 header.

        """
        if not version:
            version = self.version
        if version == 1:
            header = ("%(url)s %(ip_address)s %(date)s "
                      "%(content_type)s %(length)s")
        elif version == 2:
            header = ("%(url)s %(ip_address)s %(date)s %(content_type)s "
                      "%(result_code)s %(checksum)s %(location)s %(offset)s "
                      "%(filename)s %(length)s")

        header = header % dict(self)
        f.write(header)

    @property
    def url(self):
        return self["url"]

    @property
    def ip_address(self):
        return self["ip_address"]

    @property
    def date(self):
        return datetime.datetime.strptime(self['date'], "%Y%m%d%H%M%S")

    @property
    def content_type(self):
        return self["content_type"]

    @property
    def result_code(self):
        return self["result_code"]

    @property
    def checksum(self):
        return self["checksum"]

    @property
    def location(self):
        return self["location"]

    @property
    def offset(self):
        return int(self["offset"])

    @property
    def filename(self):
        return self["filename"]

    @property
    def length(self):
        return int(self["length"])

    def __str__(self):
        f = io.StringIO()
        self.write_to(f)
        return f.getvalue()

    def __repr__(self):
        f = {}
        fields = ("url ip_address date content_type result_code checksum "
                  "location offset filename length".split())
        for i in fields:
            if hasattr(self, i):
                f[i] = getattr(self, i)
        s = ['%s = "%s"' % (k, v) for k, v in f.items()]
        s = ", ".join(s)
        return "<ARCHeader(%s)>" % s


class ARCRecord(object):
    def __init__(self, header=None, payload=None, headers={}, version=None):
        if not (header or headers):
            raise TypeError("Can't write create an ARC1 record "
                            "without a header")
        self.header = header or ARCHeader(version=version, **headers)
        self.payload = io.BytesIO(payload)
        self.version = version
        self._read_html_headers()

    def _read_html_headers(self):
        line = self.payload.readline().decode('utf-8')
        if not line.startswith("HTTP/1"):
            self.payload.seek(0)
            return

        line = line.strip()
        headers = {
            'protocol': line,
            'status_code': status_code(line),
        }
        for line in self.payload:
            line = line.decode('utf-8')
            if not line.strip():
                break
            name, content = line.split(':', 1)
            name = name.strip()
            content = content.strip()
            headers[name.lower()] = content
        self.header['http_headers'] = headers
        self.payload = io.BytesIO(self.payload.read())

    @classmethod
    def from_string(cls, string, version):
        """
        Constructs an ARC record from a string and returns it.

        TODO: It might be best to merge this with the _read_arc_record
        function rather than reimplement the functionality here.
        """
        header, payload = string.split("\n", 1)
        if payload[0] == '\n':  # There's an extra
            payload = payload[1:]
        if int(version) == 1:
            arc_header_re = ARC1_HEADER_RE
        elif int(version) == 2:
            arc_header_re = ARC2_HEADER_RE

        matches = arc_header_re.search(header)
        headers = matches.groupdict()
        arc_header = ARCHeader(**headers)
        return cls(header=arc_header, payload=payload, version=version)

    def write_to(self, f, version=None):
        version = version or self.version or 2
        self.header.write_to(f, version)
        f.write("\n")  # This separates the header and the body
        # Usually used for small payloads
        if isinstance(self.payload, str):
            f.write(self.payload)
        # Used for large payloads where we give a file like object
        elif hasattr(self.payload, "read"):
            # Read 10MB by 10MB
            chunk_size = 10 * 1024 * 1024
            d = self.payload.read(chunk_size)
            while d:
                f.write(d)
                d = self.payload.read(chunk_size)
        f.write("\n")

    def __getitem__(self, name):
        return self.header[name]

    def __setitem__(self, name, value):
        self.header[name] = value

    def __str__(self):
        f = io.StringIO()
        self.write_to(f)
        return f.getvalue()


class ARCFile(object):
    def __init__(self, filename=None, mode=None, fileobj=None, version=None,
                 file_headers=None, compress=None):
        """
        Initialises a file like object that can be used to read or
        write Arc files. Works for both version 1 or version 2.

        This can be called similar to the builtin `file` constructor.

        It can also just be given a fileobj which is a file like
        object that it will use directly for its work.

        The file_headers should contain the following fields used to
        create the header for the file. The exact fields used depends
        on whether v1 or v2 files are being created. If a read is
        done, the headers will be autopopulated from the first record.

           * ip_address - IP address of the machine doing the Archiving
           * date - Date of archival
           * org - Organisation that's doing the Archiving.

        The version parameter tries to work intuitively as follows

            * If version is set to 'n' (where n is 1 or 2), the
              library configures itself to read and write version n
              ARC files.

                  * When we try to write a record, it will generate
                    and write a version n record.

                  * When we try to read a record, it will attempt to
                    parse it as a version n record and will error out
                    if the format is different.

            * If the version is unspecified, the library will
              configures itself as follows

                  * When we try to write a record, it will generate
                    and write a version 2 record.

                  * When we try to read a record, it will read out one
                    record and try to guess the version from it (for
                    the first read).

        """
        if fileobj is None:
            fileobj = builtins.open(filename, mode or "rb")
            mode = fileobj.mode
        # initialize compress based on filename, if not already specified
        if compress is None and filename and filename.endswith(".gz"):
            compress = True

        if compress:
            fileobj = gzip.open(fileobj, mode)

        self.fileobj = fileobj

        self.filename = filename
        if self.filename is None:
            if hasattr(self.fileobj, "name"):
                self.filename = self.fileobj.name
            else:
                self.filename = ""

        if version and int(version) not in (1, 2):
            raise TypeError("ARC version has to be 1 or 2")
        self.version = version
        self.file_headers = file_headers or {}
        self.header_written = False
        self.header_read = False
        self.file_meta = ''

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def _write_header(self):
        "Writes out an ARC header"
        if "org" not in self.file_headers:
            warnings.warn("Using 'unknown' for Archiving organisation name")
            self.file_headers['org'] = "Unknown"
        if "date" not in self.file_headers:
            now = datetime.datetime.utcnow()
            warnings.warn("Using '%s' for Archiving time" % now)
            self.file_headers['date'] = now
        if "ip_address" not in self.file_headers:
            warnings.warn("Using '127.0.0.1' as IP address of machine "
                          "that's archiving")
            self.file_headers['ip_address'] = "127.0.0.1"
        if self.version == 1:
            payload = ("1 0 %s\nURL IP-address Archive-date Content-type "
                       "Archive-length") % self.file_headers['org']
        elif self.version == 2:
            payload = ("2 0 %s\nURL IP-address Archive-date Content-type "
                       "Result-code Checksum Location Offset Filename "
                       "Archive-length" % self.file_headers['org'])
        else:
            raise IOError("Can't write an ARC file "
                          "with version '\"%s\"'" % self.version)

        fname = os.path.basename(self.filename)
        header = ARCHeader(url="filedesc://%s" % fname,
                           ip_address=self.file_headers['ip_address'],
                           date=self.file_headers['date'],
                           content_type="text/plain",
                           length=len(payload),
                           result_code="200",
                           checksum="-",
                           location="-",
                           offset=str(self.fileobj.tell()),
                           filename=fname)
        arc_file_header_record = ARCRecord(header, payload % self.file_headers)
        arc_file_header_record.write_to(self.fileobj, self.version)
        self.fileobj.write("\n")  # record separator

    def write(self, arc_record):
        "Writes out the given arc record to the file"
        if not self.version:
            self.version = 2
        if not self.header_written:
            self.header_written = True
            self._write_header()
        arc_record.write_to(self.fileobj, self.version)
        self.fileobj.write("\n")  # Record separator

    def _read_file_header(self):
        """Reads out the file header for the arc file. If version was
        not provided, this will autopopulate it."""
        header = self.fileobj.readline().decode('utf-8')
        payload1 = self.fileobj.readline().decode('utf-8')
        payload2 = self.fileobj.readline().decode('utf-8')
        version, reserved, organisation = payload1.split(maxsplit=2)
        self.header_read = True
        version = int(version)
        # print("--------------------------------------------------")
        # print(header, "\n", payload1, "\n", payload2, "\n", version)
        # print("--------------------------------------------------")
        if self.version and int(self.version) != version:
            raise IOError("Version mismatch. Requested version was '%s' but "
                          "version in file was '%s'" % (self.version, version))

        if version == 1:
            url, ip_address, date, content_type, length = header.split()
            self.file_headers = {
                "ip_address": ip_address,
                "date": datetime.datetime.strptime(date, "%Y%m%d%H%M%S"),
                "org": organisation,
                "url": url,
                'content_type': content_type,
                'length': int(length),
            }
            self.version = 1
        elif version == 2:
            (url, ip_address, date, content_type, result_code,
             checksum, location, offset, filename, length) = header.split()
            self.file_headers = {
                "ip_address": ip_address,
                "date": datetime.datetime.strptime(date, "%Y%m%d%H%M%S"),
                "org": organisation,
                'url': url,
                'content_type': content_type,
                'length': int(length),
                'filename': filename,
                'location': location,
            }
            self.version = 2
        else:
            raise IOError("Unknown ARC version '%s'" % version)

        length = int(length)
        current_size = len(payload1 + payload2)
        self.file_meta = b''
        while current_size < length:
            line = self.fileobj.readline()
            self.file_meta = self.file_meta + line
            current_size = current_size + len(line)
        self.fileobj.readline()  # Lose the separator newline

    def _strip_initial_new_lines(self):
        line = self.fileobj.readline()
        while line and not line.strip():
            line = self.fileobj.readline()
        return line.decode('utf-8').strip()

    def _safe_from_arcmetadata(self, line):
        # JG: this block stops the header parser / reader
        # from getting caught on the <arcmetadata> XML lump
        # that can appear in ARC files
        if line.startswith("<arcmetadata"):
            while not line.endswith("</arcmetadata>\n"):
                line = self.fileobj.readline().decode('utf-8')
            line = self.fileobj.readline().decode('utf-8')
            line = self.fileobj.readline().decode('utf-8')
        return line.strip()

    def _read_record_header(self, line):
        if self.version == 1:
            arc_header_re = ARC1_HEADER_RE
        elif self.version == 2:
            arc_header_re = ARC2_HEADER_RE

        matches = arc_header_re.search(line)
        headers = matches.groupdict()
        return ARCHeader(**headers)

    def _read_arc_record(self):
        "Reads out an arc record, formats it and returns it"
        # XXX:Noufal Stream payload here rather than just read it
        # r = self.fileobj.readline() # Drop the initial newline
        # if r == "":
        #     return None
        # header = self.fileobj.readline()

        line = self._strip_initial_new_lines()
        line = self._safe_from_arcmetadata(line)

        if not line:
            return None

        header = self._read_record_header(line)
        payload = self.fileobj.read(header['length'])

        self.fileobj.readline()  # Munge the separator newline.
        return ARCRecord(header=header, payload=payload)

    def read(self):
        "Reads out an arc record from the file"
        if not self.header_read:
            self._read_file_header()
        return self._read_arc_record()

    # For compatability with WARCFile
    read_record = read
    write_record = write

    def __iter__(self):
        record = self.read()
        while record:
            yield record
            record = self.read()

    def close(self):
        self.fileobj.close()
