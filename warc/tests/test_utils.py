from ..utils import FilePart, CaseInsensitiveDict
import io

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

class TestFilePart:
    def setup(self):
        # 5 chars in each line
        self.text = b"\n".join([b"aaaa", b"bbbb", b"cccc", b"dddd", b"eeee", b"ffff"])

    def test_read(self):
        part = FilePart(io.BytesIO(self.text), 0)
        assert part.read() == b""

        part = FilePart(io.BytesIO(self.text), 5)
        assert part.read() == b"aaaa\n"

        part = FilePart(io.BytesIO(self.text), 10)
        assert part.read() == b"aaaa\nbbbb\n"

        # try with large data
        part = FilePart(io.BytesIO(b"a" * 10000), 10)
        assert len(part.read()) == 10

    def test_read_with_size(self):
        part = FilePart(io.BytesIO(self.text), 10)
        assert part.read(3) == b"aaa"
        assert part.read(3) == b"a\nb"
        assert part.read(3) == b"bbb"
        assert part.read(3) == b"\n"
        assert part.read(3) == b""

    def test_read_with_buffer(self):
        "Tests read size when read length is larger than buffer."
        fb = io.BytesIO(b'a' * 10000)
        part = FilePart(fb, 10000)
        temp = part.read(100)
        part._unread(temp)
        assert len(part.read(1000)) == 1000

    def test_readline(self):
        part = FilePart(io.BytesIO(self.text), 11)
        assert part.readline() == b"aaaa\n"
        assert part.readline() == b"bbbb\n"
        assert part.readline() == b"c"
        assert part.readline() == b""

    def test_iter(self):
        part = FilePart(io.BytesIO(self.text), 11)
        assert list(part) == [b"aaaa\n", b"bbbb\n", b"c"]
