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

    
def test_sample_data():
    import gzip
    f = gzip.GzipFile("test_data/alexa_short_header.arc.gz")
    a = ARCFile(fileobj = f)
    record = str(a.read())
    expected = """http://www.killerjo.net:80/robots.txt 211.111.217.29 20110804181142       39
SSH-2.0-OpenSSH_5.3p1 Debian-3ubuntu3\r\n\n"""
    assert record == expected


    

