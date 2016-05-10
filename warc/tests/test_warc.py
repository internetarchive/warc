from ..warc import WARCReader, WARCHeader, WARCRecord, WARCFile
import io

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
    b"WARC/1.0\r\n" +
    b"Content-Length: 10\r\n" +
    b"WARC-Date: 2012-02-10T16:15:52Z\r\n" +
    b"Content-Type: application/http; msgtype=response\r\n" +
    b"WARC-Type: response\r\n" +
    b"WARC-Record-ID: <urn:uuid:80fb9262-5402-11e1-8206-545200690126>\r\n" +
    b"WARC-Target-URI: http://example.com/\r\n" +
    b"\r\n" +
    b"Helloworld" +
    b"\r\n\r\n"
)

class TestWARCReader:
    def test_read_header1(self):
        f = io.BytesIO(SAMPLE_WARC_RECORD_TEXT)
        h = WARCReader(f).read_record().header
        assert h.date == "2012-02-10T16:15:52Z"
        assert h.record_id == "<urn:uuid:80fb9262-5402-11e1-8206-545200690126>"
        assert h.type == "response"
        assert h.content_length == 10

    def test_empty(self):
        reader = WARCReader(io.BytesIO(b""))
        assert reader.read_record() is None

    def test_read_record(self):
        f = io.BytesIO(SAMPLE_WARC_RECORD_TEXT)
        reader = WARCReader(f)
        record = reader.read_record()
        assert record.payload.readline() == b"Helloworld"

    def read_multiple_records(self):
        f = io.BytesIO(SAMPLE_WARC_RECORD_TEXT * 5)
        reader = WARCReader(f)
        for i in range(5):
            rec = reader.read_record()
            assert rec is not None

class TestWarcFile:
    def test_read(self):
        f = WARCFile(fileobj=io.BytesIO(SAMPLE_WARC_RECORD_TEXT))
        assert f.read_record() is not None
        assert f.read_record() is None

    def test_long_header(self):
        """Test large WARC header with a CRLF across a 1024 byte boundrary"""
        from .. import warc
        import os.path
        warc_dir = os.path.dirname(warc.__file__)
        file = os.path.join(warc_dir, '../test_data/crlf_at_1k_boundary.warc.gz')
        f = WARCFile(file)
        h = f.read_record().header
        assert h['WARC-Payload-Digest'] == "sha1:M4VJCCJQJKPACSSSBHURM572HSDQHO2P"

if __name__ == '__main__':
    TestWARCReader().test_read_header()
