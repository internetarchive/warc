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


def warc_to_zip():
    warcfile = sys.argv[1]
    zipout = sys.argv[2]

    file = zipfile.ZipFile(zipout, "w", zipfile.ZIP_DEFLATED, True)

    f = warc.WARCFile( warcfile, "rb" )
    for record in f:
        print "------------"
        for key in record.header.keys():
            print key,record.header[key]
        if record.header.has_key('warc-target-uri'):
            u = urlparse(record['WARC-Target-URI'])
            name = "{}/{}/{}".format(u.scheme, u.netloc, u.path )
            if record['content-type'] == "application/http;msgtype=response":
                r = httpparse(record.payload)
                file.writestr(name, r.read())
            elif record['content-type'] == "application/http;msgtype=request":
                print "payload:",record.payload
                print "Skipping request record", record['WARC-Target-URI']
                file.writestr("{}-request".format(name), record.payload.read())
            else:
                print "Skipping record", record['WARC-Target-URI']
                file.writestr(name, record.payload.read())


    file.close()

if __name__ == '__main__':
    warc_to_zip()
