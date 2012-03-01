"""
Provides support for Arc v1 files. 

:copyright: (c) 2012 Internet Archive
"""

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

        
class ArcRecord(object):
    def __init__(self, header = None, payload = None, headers = {}):
        if not (header or headers):
            raise TypeError("Can't write create an Arc1 record without a header")
        self.header = header or ArcHeader(**headers)
        self.payload = payload
        
        
        
    
