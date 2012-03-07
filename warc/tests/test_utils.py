from ..utils import FilePart
from cStringIO import StringIO

class TestFilePart:
    def setup_method(self, m):
        # 5 chars in each line
        self.text = "\n".join(["aaaa", "bbbb", "cccc", "dddd", "eeee", "ffff"])
        
    def test_read(self):
        part = FilePart(StringIO(self.text), 0)
        assert part.read() == ""
    
        part = FilePart(StringIO(self.text), 5)
        assert part.read() == "aaaa\n"

        part = FilePart(StringIO(self.text), 10)
        assert part.read() == "aaaa\nbbbb\n"
        
        # try with large data
        part = FilePart(StringIO("a" * 10000), 10)
        assert len(part.read()) == 10
        
    def test_read_with_size(self):
        part = FilePart(StringIO(self.text), 10)
        assert part.read(3) == "aaa"
        assert part.read(3) == "a\nb"
        assert part.read(3) == "bbb"
        assert part.read(3) == "\n"
        assert part.read(3) == ""
        
    def test_readline(self):
        part = FilePart(StringIO(self.text), 11)
        assert part.readline() == "aaaa\n"
        assert part.readline() == "bbbb\n"
        assert part.readline() == "c"
        assert part.readline() == ""
        
    def test_iter(self):
        part = FilePart(StringIO(self.text), 11)
        assert list(part) == ["aaaa\n", "bbbb\n", "c"]