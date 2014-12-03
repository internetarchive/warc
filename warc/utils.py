"""
warc.utils
~~~~~~~~~~

This file is part of warc

:copyright: (c) 2012 Internet Archive
"""

from collections import MutableMapping
from http.client import parse_headers

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

    def read(self, size=-1):
        if size == -1:
            size = self.length

        if len(self.buf) >= size:
            content = self.buf[:size]
            self.buf = self.buf[size:]
        else:
            size = min(size, self.length - self.offset)
            content = self.buf + self.fileobj.read(size - len(self.buf))
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
    def __init__(self, request_file):
        #Parse version line
        id_str_raw = request_file.readline()
        id_str = self.id_str_raw.decode("iso-8859-1")
        if "HTTP" not in id_str:
            #This is not an HTTP object.
            request_file._unread(self.id_str_raw)
            raise ValueError("Object is not HTTP.")
            
        words = id_str.split()
        command = path = status = error = version = None
        #If length is not 3 it is a bad version line.
        if len(words) >= 3:
            if words[1].isdigit():
                version = words[0]
                error = words[1]
                status = " ".join(words[2:])
            else:
                command, path, version = words
        
        self._id = {
            "vline": id_str,
            "command": command,
            "path": path,
            "status": status,
            "error": error,
            "version": version,
        }
        
        self._header = parse_headers(request_file)
        super().__init__(self._header)
        self.payload = request_file
    
    def __repr__(self):
        return(self.vline + str(self._header))
        
    def __getitem__(self, name):
        try:
            return super().__getitem__(name)
        except KeyError:
            value = name.lower()
            if value == "content_type":
                return self.content_type
            elif value == "charset":
                return self.charset
            elif value == "host":
                return self.host
            elif value in self._id:
                return self._id[value]
            else:
                raise

    def _reset(self):
        self.payload._unread("\r\n".encode())
        for i in self._header:
            value = i + ": " + self._header[i] + "\r\n"
            self.payload._unread(value.encode())
        self.payload._unread(self.vline.encode())

    @property
    def vline(self):
        return self._id["vline"]

    @property
    def version(self):
        return self._id["version"]

    #Request
    @property
    def command(self):
        return self._id["command"]

    @property
    def path(self):
        return self._id["path"]

    @property
    def host(self):
        try:
            return self._d['host']
        except:
            return None

    #Response
    @property
    def status(self):
        return self._id["status"]

    @property
    def error(self):
        value = self._id["error"]
        return int(value) if value else value

    #Inherited from email parser.
    @property
    def content_type(self):
        return self._header.get_content_type()

    @property
    def charset(self):
        return self._header.get_content_charset()

    #Havn't used it yet.
    def get_payload(self, size=1024):
        encoding = self._header.get("Transfer-Encoding", "None")
        if encoding == "chunked":
            found = b''
            length = int(str(self.payload.readline(), "iso-8859-1").rstrip("\r\n"), 16)
            while length > 0:
                found += self.payload.read(length)
                self.payload.readline()
                length = int(str(self.payload.readline(), "iso-8859-1").rstrip("\r\n"), 16)

            return found

        length = int(self._header.get("Content-Length", -1))
        return self.payload.read(length)
