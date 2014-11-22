"""
warc.utils
~~~~~~~~~~

This file is part of warc

:copyright: (c) 2012 Internet Archive
"""

from collections import MutableMapping


class CaseInsensitiveDict(MutableMapping):
    """Almost like a dictionary, but keys are case-insensitive.
    
        >>> d = CaseInsensitiveDict(foo=1, Bar=2)
        >>> d['foo']
        1
        >>> d['bar']
        2
        >>> d['Foo'] = 11
        >>> d['FOO']
        11
        >>> d.keys()
        ["foo", "bar"]
    """
    def __init__(self, *args, **kwargs):
        self._d = {}
        self.update(dict(*args, **kwargs))
        
    def __setitem__(self, name, value):
        self._d[name.lower()] = value
    
    def __getitem__(self, name):
        return self._d[name.lower()]
        
    def __delitem__(self, name):
        del self._d[name.lower()]
        
    def __eq__(self, other):
        return isinstance(other, CaseInsensitiveDict) and other._d == self._d
        
    def __iter__(self):
        return iter(self._d)
        
    def __len__(self):
        return len(self._d)

class FilePart:
    """File interface over a part of file.
    
    Takes a file and length to read from the file and returns a file-object 
    over that part of the file.
    """
    def __init__(self, fileobj, length):
        self.fileobj = fileobj
        self.length = length
        self.offset = 0
        self.buf = b'' 
        
    def read(self, size):
        if size == -1:
            size = self.length
        
        if len(self.buf) >= size:
            content = self.buf[:size]
            self.buf = self.buf[size:]
        else:
            size = min(size, self.length - self.offset - len(self.buf))
            content = self.buf + self.fileobj.read(size)
            self.buf = b''
        self.offset += len(content)
        return content
        
    def _unread(self, content):
        self.buf = content + self.buf
        self.offset -= len(content)
        
    def readline(self, size=1024):
        chunks = []
        chunk = self.read(size)
        while chunk and b"\n" not in chunk:
            chunks.append(chunk)
            chunk = self.read(size)
            
        if b"\n" in chunk:
            index = chunk.index(b"\n")
            self._unread(chunk[index+1:])
            chunk = chunk[:index+1]
        chunks.append(chunk)
        return b"".join(chunks)

    def __iter__(self):
        line = self.readline()
        while line:
            yield line
            line = self.readline()
            
class HTTPObject(CaseInsensitiveDict):
    """Small object to help with parsing HTTP warc entries"""
    def __init__(self, file):
        
        #Parse version line
        id_Str = file.readline().decode("iso-8859-1")
        words = id_str.split()
        command = path = status = error = version = None
        #If length is not 3 it is a bad version line.
        if len(words) == 3:
            if words[1].isdigit():
                version, error, status = words
            else:
                command, path, version = words
        
        self.id = {
            "raw": id_Str,
            "command": command,
            "path": path,
            "status": status,
            "error": error,
            "version": version,
        }
        
        self.header = parse_headers(request_file)
        super().__init__(self.header)
        
        self.payload = request_file
    
    def _parseversion(self):
    
    @property
    def vline(self):
        return self.id["raw"]    
    
    @property
    def command(self):
        return self.id["command"]

    @property
    def path(self):
        return self.id["path"]

    @property
    def status(self):
        return self.id["status"]

    @property
    def error(self):
        value = self.id["error"]
        return int(value) if value else value

    @property
    def version(self):
        return self.id["version"]

    @property
    def content_type(self):
        return self.header.get_content_type()
        
    @property
    def charset(self):
        return self.header.get_content_charset()
        
    def read(self, size=1024):
        encoding = self.header.get("Transfer-Encoding", "None")
        if encoding == "chunked":
            found = b''
            length = int(str(self.payload.readline(), "iso-8859-1").rstrip("\r\n"), 16)
            while length > 0:
                found += self.payload.read(length)
                self.payload.readline()
                length = int(str(self.payload.readline(), "iso-8859-1").rstrip("\r\n"), 16)
        
            return found
                
        else:
            length = self.header.get("Content-Length", -1)
            return self.payload.read(length)
