from . import arc1

import pytest

def test_create_arc1_header():
    "Make sure Header can be created only with expected fields"
    with pytest.raises(TypeError):
        arc1.Arc1Header()

    with pytest.raises(TypeError):
        arc1.Arc1Header(test="1234")
    
def test_arc1_header_attributes():
    "Make sure that Arc header fields are accessible as attributes"
    header = arc1.Arc1Header(url = "http://www.archive.org",
                             ip_address = "127.0.0.1", 
                             date = "20120301093000", 
                             content_type = "text/html", 
                             length = "500")
    
    assert header.url == "http://www.archive.org"
    assert header.ip_address == "127.0.0.1"
    assert header.date == "20120301093000"
    assert header.content_type == "text/html"
    assert header.length == 500
    
