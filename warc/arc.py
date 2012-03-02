"""
Provides support for Arc v1 files. 

:copyright: (c) 2012 Internet Archive
"""

import StringIO

from .utils import CaseInsensitiveDict

class ArcHeader(CaseInsensitiveDict):
    """
    Holds fields from an Arc V1 or V2 header.
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

        header =  header%dict(url          = self.url,
                              ip_address   = self.ip_address,
                              date         = self.date,
                              content_type = self.content_type,
                              result_code  = self.result_code,
                              checksum     = self.checksum,
                              location     = self.location,
                              offset       = self.offset,
                              filename     = self.filename,
                              length       = self.length)
        f.write(header)
            

    @property
    def url(self):
        return self["url"]
    
    @property
    def ip_address(self):
        return self["ip_address"]
    
    @property
    def date(self):
        return self["date"]
    
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
        return "<ArcHeader(%s)>"%s

        
class ArcRecord(object):
    def __init__(self, header = None, payload = None, headers = {}):
        if not (header or headers):
            raise TypeError("Can't write create an Arc1 record without a header")
        self.header = header or ArcHeader(**headers)
        self.payload = payload
    
    def write_to(self, f, version = 2):
        f.write("\n")
        self.header.write_to(f, version)
        f.write("\n")
        f.write(self.payload)
        
        
        
    
