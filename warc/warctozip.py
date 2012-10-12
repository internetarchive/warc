#!/usr/bin/env python
import warc
import zipfile
from optparse import OptionParser
import sys
from StringIO import StringIO
from httplib import HTTPResponse
from urlparse import urlparse

class FakeSocket(StringIO):
    def makefile(self, *args, **kw):
        return self

def httpparse(fp):
    socket = FakeSocket(fp.read())
    response = HTTPResponse(socket)
    response.begin()
    return response


print sys.argv[1] 
file = zipfile.ZipFile("test.zip", "w")

f = warc.open( sys.argv[1])
for record in f:
    print record.header.keys()
    if record.header.has_key('warc-target-uri'):
        u = urlparse(record['WARC-Target-URI'])
        name = "{}{}".format(u.scheme, u.path)
        r = httpparse(record.payload)
        file.writestr(name, r.read())

file.close()
