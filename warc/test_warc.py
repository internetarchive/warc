from . import WARCReader, WARCHeader, CaseInsensitiveDict, WARCFile

from StringIO import StringIO

class TestCaseInsensitiveDict:
    def test_all(self):
        d = CaseInsensitiveDict()
        d['Foo'] = 1
        assert d['foo'] == 1
        assert 'foo' in d
        assert 'Foo' in d

        assert 'bar' not in d
        d['BAR'] = 2
        assert 'bar' in d
        assert d['bar'] == 2
        
        assert sorted(d.keys()) == ["bar", "foo"]
        assert sorted(d.items()) == [("bar", 2), ("foo", 1)]
        
class TestWARCHeader:
    def test_attrs(self):
        h = WARCHeader({
            "WARC-Type": "response",
            "WARC-Record-ID": "<record-1>",
            "WARC-Date": "2000-01-02T03:04:05Z",
            "Content-Length": "10"
        })
        assert h.type == "response"
        assert h.record_id == "<record-1>"
        assert h.date == "2000-01-02T03:04:05Z"
        assert h.content_length == 10
        
    def test_item_access(self):
        h = WARCHeader({
            "WARC-Type": "response",
            "X-New-Header": "42"
        })
        assert h['WARC-Type'] == "response"
        assert h['WARC-TYPE'] == "response"
        assert h['warc-type'] == "response"

        assert h['X-New-Header'] == "42"
        assert h['x-new-header'] == "42"
        
    def test_str(self):
        h = WARCHeader({})
        assert str(h) == "WARC/1.0\r\n\r\n"

        h = WARCHeader({
            "WARC-Type": "response"
        })
        assert str(h) == "WARC/1.0\r\n" + "WARC-Type: response\r\n\r\n"
        
    def test_init_defaults(self):
        # It should initialize all the mandatory headers
        h = WARCHeader({"WARC-Type": "resource"}, defaults=True)
        assert h.type == "resource"
        assert "WARC-Date" in h
        assert "Content-Length" in h
        assert "Content-Type" in h
        assert "WARC-Record-ID" in h

    def test_new_content_types(self):
        def f(type): 
            return WARCHeader({"WARC-Type": type}, defaults=True)
        assert f("response")["Content-Type"] == "application/http; msgtype=response"
        assert f("request")["Content-Type"] == "application/http; msgtype=request"
        assert f("warcinfo")["Content-Type"] == "application/warc-fields"
        assert f("newtype")["Content-Type"] == "application/octet-stream"

SAMPLE_WARC_RECORD_TEXT = (
    "WARC/1.0\r\n" +
    "Content-Length: 10\r\n" +
    "WARC-Date: 2012-02-10T16:15:52Z\r\n" +
    "Content-Type: application/http; msgtype=response\r\n" +
    "WARC-Type: response\r\n" +
    "WARC-Record-ID: <urn:uuid:80fb9262-5402-11e1-8206-545200690126>\r\n" +
    "WARC-Target-URI: http://example.com/\r\n" +
    "\r\n" +
    "Helloworld" +
    "\r\n\r\n"
)

class TestWARCReader:
    def test_read_header1(self):
        text = (
            "WARC/1.0\r\n" +
            "Content-Length: 10\r\n" +
            "WARC-Date: 2012-02-10T16:15:52Z\r\n" +
            "Content-Type: application/http; msgtype=response\r\n" +
            "WARC-Type: response\r\n" +
            "WARC-Record-ID: <urn:uuid:80fb9262-5402-11e1-8206-545200690126>\r\n" +
            "WARC-Target-URI: http://example.com/\r\n" +
            "\r\n"
        )
        f = StringIO(str(text))
        h = WARCReader(f).read_header()
        assert h.date == "2012-02-10T16:15:52Z"
        assert h.record_id == "<urn:uuid:80fb9262-5402-11e1-8206-545200690126>"
        assert h.type == "response"
        assert h.content_length == 10
        
    def test_read_header(self):
        h = WARCHeader({"WARC-Type": "response"}, defaults=True)
        f = StringIO(str(h))
        h2 = WARCReader(f).read_header()
        assert h == h2
        
    def test_empty(self):
        reader = WARCReader(StringIO(""))
        assert reader.read_header() is None
        assert reader.read_record() is None
    
    def test_read_record(self):
        text = (
            "WARC/1.0\r\n" +
            "Content-Length: 10\r\n" +
            "WARC-Date: 2012-02-10T16:15:52Z\r\n" +
            "Content-Type: application/http; msgtype=response\r\n" +
            "WARC-Type: response\r\n" +
            "WARC-Record-ID: <urn:uuid:80fb9262-5402-11e1-8206-545200690126>\r\n" +
            "WARC-Target-URI: http://example.com/\r\n" +
            "\r\n" +
            "Helloworld" +
            "\r\n\r\n"
        )
        f = StringIO(text)
        reader = WARCReader(f)
        record = reader.read_record()
        assert record.payload == "Helloworld"
        
    def read_multiple_records(self):
        text = (
            "WARC/1.0\r\n" +
            "Content-Length: 10\r\n" +
            "WARC-Date: 2012-02-10T16:15:52Z\r\n" +
            "Content-Type: application/http; msgtype=response\r\n" +
            "WARC-Type: response\r\n" +
            "WARC-Record-ID: <urn:uuid:80fb9262-5402-11e1-8206-545200690126>\r\n" +
            "WARC-Target-URI: http://example.com/\r\n" +
            "\r\n" +
            "Helloworld" +
            "\r\n\r\n"
        )
        f = StringIO(text * 5)
        reader = WARCReader(f)
        for i in range(5):
            rec = reader.read_record()
            assert rec is not None
            
        f = StringIO(text * 5)
        # test __iter__
        assert len(list(f)) == 5
        
class TestWarcFile:
    def test_read(self):
        f = WARCFile(fileobj=StringIO(SAMPLE_WARC_RECORD_TEXT))
        assert f.read() is not None
        assert f.read() is None
    
if __name__ == '__main__':
    TestWARCReader().test_read_header()