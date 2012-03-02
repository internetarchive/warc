import StringIO

from . import arc

import pytest

def test_init_arc_header():
    "Make sure Header can be initialise only with expected fields"
    with pytest.raises(TypeError):
        arc.ARCHeader(test="1234")
    
def test_arc_header_attributes():
    "Make sure that ARC1 header fields are accessible as attributes"
    header = arc.ARCHeader(url = "http://archive.org",
                           ip_address = "127.0.0.1", 
                           date = "20120301093000", 
                           content_type = "text/html", 
                           length = "500",
                           result_code = "200",
                           checksum = "a123456", 
                           location = "http://www.archive.org",
                           offset = "300",
                           filename = "sample.arc.gz")
    
    assert header.url == "http://archive.org"
    assert header.ip_address == "127.0.0.1"
    assert header.date == "20120301093000"
    assert header.content_type == "text/html"
    assert header.length == 500
    assert header.result_code == "200"
    assert header.checksum == "a123456"
    assert header.location == "http://www.archive.org"
    assert header.offset == 300
    assert header.filename == "sample.arc.gz"
    
def test_arc_v1_header_creation():
    "Validate ARC V1 header creation"
    header = arc.ARCHeader(url = "http://archive.org",
                           ip_address = "127.0.0.1", 
                           date = "20120301093000", 
                           content_type = "text/html", 
                           length = "500",
                           result_code = "200",
                           checksum = "a123456", 
                           location = "http://www.archive.org",
                           offset = "300",
                           filename = "sample.arc.gz")
    f = StringIO.StringIO()
    header.write_to(f, 1)
    header_v1_string = f.getvalue()
    assert header_v1_string == "http://archive.org 127.0.0.1 20120301093000 text/html 500\n"
    
    
def test_arc_v2_header_creation():
    "Validate ARC V2 header creation"
    header = arc.ARCHeader(url = "http://archive.org",
                           ip_address = "127.0.0.1", 
                           date = "20120301093000", 
                           content_type = "text/html", 
                           length = "500",
                           result_code = "200",
                           checksum = "a123456", 
                           location = "http://www.archive.org",
                           offset = "300",
                           filename = "sample.arc.gz")
    f = StringIO.StringIO()
    header.write_to(f)
    header_v2_string = f.getvalue()
    assert header_v2_string == "http://archive.org 127.0.0.1 20120301093000 text/html 200 a123456 http://www.archive.org 300 sample.arc.gz 500\n"
    
    
def test_arc_v1_record_creation():
    "Validate ARC V1 record creation"
    header = arc.ARCHeader(url = "http://archive.org",
                           ip_address = "127.0.0.1", 
                           date = "20120301093000", 
                           content_type = "text/html", 
                           length = "500",
                           result_code = "200",
                           checksum = "a123456", 
                           location = "http://www.archive.org",
                           offset = "300",
                           filename = "sample.arc.gz")
    record_v1 = arc.ARCRecord(header, "BlahBlah")
    f = StringIO.StringIO()
    record_v1.write_to(f)
    record_v1_string = f.getvalue()
    assert record_v1_string == "\nhttp://archive.org 127.0.0.1 20120301093000 text/html 200 a123456 http://www.archive.org 300 sample.arc.gz 500\n\nBlahBlah"

def test_arc_v2_record_creation():
    "Validate ARC V1 record creation"
    header = dict(url = "http://archive.org",
                  ip_address = "127.0.0.1", 
                  date = "20120301093000", 
                  content_type = "text/html", 
                  length = "500",
                  result_code = "200",
                  checksum = "a123456", 
                  location = "http://www.archive.org",
                  offset = "300",
                  filename = "sample.arc.gz")
    record_v1 = arc.ARCRecord(payload = "BlahBlah", headers = header)
    f = StringIO.StringIO()
    record_v1.write_to(f)
    record_v1_string = f.getvalue()
    assert record_v1_string == "\nhttp://archive.org 127.0.0.1 20120301093000 text/html 200 a123456 http://www.archive.org 300 sample.arc.gz 500\n\nBlahBlah"

    

    


    
