from ..__init__ import open as libopen
from ..warc import WARCFile

import os

def test_open_warc_file():
    "Test opening a WARC file"

    f = libopen("foo.warc","wb")
    assert isinstance(f, WARCFile)
    f.close()
    os.unlink("foo.warc")

