from . import arc

import pytest

def test_create_arc1_header():
    "Make sure Header can be created only with expected fields"

    with pytest.raises(TypeError):
        arc.ArcHeader(test="1234")
    
def test_arc1_header_attributes():
    "Make sure that Arc1 header fields are accessible as attributes"
    header = arc.ArcHeader(url = "http://archive.org",
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
    
    
    

    
