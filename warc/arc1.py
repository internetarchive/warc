"""
Provides support for Arc v1 files. 

:copyright: (c) 2012 Internet Archive
"""

from .utils import CaseInsensitiveDict

class Arc1Header(CaseInsensitiveDict):
    """
    Holds fields from an Arc V1 header.
    The fields are

        * url
        * ip_address
        * date
        * content-type
        * length (length of the n/w doc in bytes)
    """
    def __init__(self, url, ip_address, date, content_type, length):
        CaseInsensitiveDict.__init__(self, 
                                     url = url, 
                                     ip_address = ip_address, 
                                     date = date, 
                                     content_type = content_type, 
                                     length = length)
    @property
    def url(self):
        return self['url']
    
    @property
    def ip_address(self):
        return self['ip_address']

    @property
    def date(self):
        return self['date']

    @property
    def content_type(self):
        return self['content_type']

    @property
    def length(self):
        return int(self['length'])
        
