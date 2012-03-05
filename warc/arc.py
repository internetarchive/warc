"""
Provides support for ARC v1 files. 

:copyright: (c) 2012 Internet Archive
"""

import __builtin__
import datetime
import os
import StringIO
import warnings

from .utils import CaseInsensitiveDict

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
    def __init__(self, url = "",  ip_address = "",  date = "",  content_type = "",  
                 result_code = "",  checksum = "",  location = "",  offset = "",  filename = "",  length = ""):

        if isinstance(date, datetime.datetime):
            date = date.strftime("%Y%m%d%H%M%S")
        try:
            datetime.datetime.strptime(date, "%Y%m%d%H%M%S")
        except ValueError:
            raise ValueError("Couldn't parse the date '%s' in file header"%date)

        CaseInsensitiveDict.__init__(self, 
                                     url = url, 
                                     ip_address = ip_address,
                                     date = date,
                                     content_type = content_type,
                                     result_code = result_code,
                                     checksum = checksum,
                                     location = location,
                                     offset = offset,
                                     filename = filename,
                                     length = length)
    
    def write_to(self, f, version = 2):
        """
        Writes out the arc header to the file like object `f`. 

        If the version field is 1, it writes out an arc v1 header,
        otherwise (and this is default), it outputs a v2 header.

        """
        if version == 1:
            header = "%(url)s %(ip_address)s %(date)s %(content_type)s %(length)s\n"
        elif version == 2:
            header = "%(url)s %(ip_address)s %(date)s %(content_type)s %(result_code)s %(checksum)s %(location)s %(offset)s %(filename)s %(length)s\n"

        header =  header%dict(url          = self['url'],
                              ip_address   = self['ip_address'],
                              date         = self['date'],
                              content_type = self['content_type'],
                              result_code  = self['result_code'],
                              checksum     = self['checksum'],
                              location     = self['location'],
                              offset       = self['offset'],
                              filename     = self['filename'],
                              length       = self['length'])
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
    def checksum (self):
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
        f = StringIO.StringIO()
        self.write_to(f)
        return f.getvalue()
        
    def __repr__(self):
        f = {}
        for i in "url ip_address date content_typeresult_code checksum location offset filename length".split():
            if hasattr(self,i):
                f[i] = getattr(self, i)
        s = ['%s = "%s"'%(k, v) for k,v in f.iteritems()]
        s = ", ".join(s)
        return "<ARCHeader(%s)>"%s

        
class ARCRecord(object):
    def __init__(self, header = None, payload = None, headers = {}):
        if not (header or headers):
            raise TypeError("Can't write create an ARC1 record without a header")
        self.header = header or ARCHeader(**headers)
        self.payload = payload
    
    def write_to(self, f, version = 2):
        f.write("\n")
        self.header.write_to(f, version)
        # XXX:Noufal
        # The header writes out a \n as part of itself. The spec says
        # that the header and payload are to be separated by another
        # newline.  This makes it different from the Alexa crawl
        # samples which don't have this extra \n
        # XXX:Noufal
        f.write("\n")
        f.write(self.payload)

    def __getitem__(self, name):
        return self.header[name]

    def __setitem__(self, name, value):
        self.header[name] = value

    
    def __str__(self):
        f = StringIO.StringIO()
        self.write_to(f)
        return f.getvalue()
        
    
class ARCFile(object):
    def __init__(self, filename=None, mode=None, fileobj=None, version = None, file_headers = {}):
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
            fileobj = __builtin__.open(filename, mode or "rb")
        self.fileobj = fileobj

        if version != None and int(version) not in (1, 2):
            raise TypeError("ARC version has to be 1 or 2")
        self.version = version
        self.file_headers = file_headers
        self.header_written = False
        self.header_read = False

        
    def _write_header(self):
        "Writes out an ARC header"
        if "org" not in self.file_headers:
            warnings.warn("Using 'unknown' for Archiving organisation name")
            self.file_headers['org'] = "Unknown"
        if "date" not in self.file_headers:
            now = datetime.datetime.utcnow()
            warnings.warn("Using '%s' for Archiving time"%now)
            self.file_headers['date'] = now
        if "ip_address" not in self.file_headers:
            warnings.warn("Using '127.0.0.1' as IP address of machine that's archiving")
            self.file_headers['ip_address'] = "127.0.0.1"
        if self.version == 1:
            payload = "1 0 %(org)s\nURL IP-address Archive-date Content-type Archive-length\n"%dict(org = self.file_headers['org'])
        elif self.version == 2:
            payload = "2 0 %(org)s\nURL IP-address Archive-date Content-type Result-code Checksum Location Offset Filename Archive-length\n"
        else:
            raise IOError("Can't write an ARC file with version '\"%s\"'"%self.version)
        
        fname = os.path.basename(self.fileobj.name)
        header = ARCHeader(url = "filedesc://%s"%fname,
                           ip_address = self.file_headers['ip_address'], 
                           date = self.file_headers['date'],
                           content_type = "text/plain", 
                           length = len(payload),
                           result_code = "200",
                           checksum = "-", 
                           location = "-",
                           offset = str(self.fileobj.tell()),
                           filename = fname)
        header.write_to(self.fileobj, version = self.version)
        self.fileobj.write(payload%self.file_headers)
        self.fileobj.write("\n")
            
    def write(self, arc_record):
        "Writes out the given arc record to the file"
        if not self.version:
            self.version = 2
        if not self.header_written:
            self._write_header()
            self.header_written = True
        arc_record.write_to(self.fileobj, self.version)

    def _read_file_header(self):
        """Reads out the file header for the arc file. If version was
        not provided, this will autopopulate it."""
        header = self.fileobj.readline()
        payload1 = self.fileobj.readline()
        payload2 = self.fileobj.readline()
        version, reserved, organisation = payload1.split(None, 2)
        self.fileobj.readline() # Lose the newline
        self.header_read = True
        
        if self.version and int(self.version) != version:
            raise IOError("Version mismatch. Requested version was '%s' but version in file was '%s'"%(self.version, version))
        
        if version == '1':
            url, ip_address, date, content_type, length = header.split()
            self.file_headers = {"ip_address" : ip_address,
                                 "date" : datetime.datetime.strptime(date, "%Y%m%d%H%M%S"),
                                 "org" : organisation}
            self.version = 1
        elif version == '2':
            url, ip_address, date, content_type, result_code, checksum, location, offset, filename, length  = header.split()
            self.file_headers = {"ip_address" : ip_address,
                                 "date" : datetime.datetime.strptime(date, "%Y%m%d%H%M%S"),
                                 "org" : organisation}
            self.version = 2
        else:
            raise IOError("Unknown ARC version '%s'"%version)

    def _read_arc_record(self):
        "Reads out an arc record, formats it and returns it"
        #XXX:Noufal Stream payload here rather than just read it
        r = self.fileobj.readline() # Drop the initial newline
        if r == "":
            return None
        header = self.fileobj.readline()
        self.fileobj.readline() # Drop the separator newline

        if self.version == 1:
            url, ip_address, date, content_type, length = header.split()
            headers = dict(url = url, ip_address = ip_address,
                           date = date, content_type = content_type,
                           length = length)
            arc_header = ARCHeader(**headers)
        elif self.version == 2:
            url, ip_address, date, content_type, result_code, checksum, location, offset, filename, length  = header.split()
            headers = dict(url = url, ip_address = ip_address, date = date, 
                           content_type = content_type, result_code = result_code, 
                           checksum = checksum, location = location, offset = offset, 
                           filename = filename, length = length)
            arc_header = ARCHeader(**headers)
        payload = self.fileobj.read(int(length))

        return ARCRecord(header = arc_header, payload = payload)
        
    def read(self):
        "Reads out an arc record from the file"
        if not self.header_read:
            self._read_file_header()
        return self._read_arc_record()

    def __iter__(self):
        record = self.read()
        while record:
            yield record
            record = self.read()
    
    def close(self):
        self.fileobj.close()
        
        
        
        
        
        
    
    
    
    
