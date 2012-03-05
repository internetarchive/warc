from .. import open as libopen
from .. import WARCFile, ARCFile

import os

import pytest

def test_open_warc_file():
    "Test opening a WARC file"
    
    f = libopen("foo.warc","wb")
    assert isinstance(f, WARCFile)
    f.close()
    os.unlink("foo.warc")


def test_open_arc_file():
    "Test opening an ARC file"
    
    f = libopen("foo.arc","wb")
    assert isinstance(f, ARCFile)
    f.close()
    os.unlink("foo.arc")


def test_open_unknown_file():
    "Test opening a WARC file"

    with pytest.raises(IOError):
        libopen("foo","wb")

    

    

