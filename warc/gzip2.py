"""Enhanced gzip library to support multiple member gzip files.

GZIP has an interesting property that contatination of mutliple gzip files is a valid gzip file. 
In other words, a gzip file can have multiple members, each individually gzip 
compressed. The members simply appear one after another in the file, with no 
additional information before, between, or after them.

See GZIP RFC for more information.

http://www.gzip.org/zlib/rfc-gzip.html

This library provides support for creating and reading multi-member gzip files.
"""
from gzip import WRITE, READ, write32u, GzipFile as BaseGzipFile
import zlib

def open(filename, mode="rb", compresslevel=9):
    """Shorthand for GzipFile(filename, mode, compresslevel).
    """
    return GzipFile(filename, mode, compresslevel)

class GzipFile(BaseGzipFile):
    """GzipFile with support for multi-member gzip files.
    """
    def __init__(self, filename=None, mode=None, 
                 compresslevel=9, fileobj=None):
        BaseGzipFile.__init__(self, 
            filename=filename, 
            mode=mode,
            compresslevel=compresslevel,
            fileobj=fileobj)
            
        if self.mode == WRITE:
            # Indicates the start of a new member if value is True.
            # The BaseGzipFile constructor already wrote the header for new 
            # member, so marking as False.
            self._new_member = False
            
        # When _member_lock is True, only one member in gzip file is read
        self._member_lock = False
    
    def close_member(self):
        """Closes the current member being written.
        """
        # The new member is not yet started, no need to close
        if self._new_member:
            return
            
        self.fileobj.write(self.compress.flush())
        write32u(self.fileobj, self.crc)
        # self.size may exceed 2GB, or even 4GB
        write32u(self.fileobj, self.size & 0xffffffffL)
        self.size = 0
        self.compress = zlib.compressobj(9,
                                         zlib.DEFLATED,
                                         -zlib.MAX_WBITS,
                                         zlib.DEF_MEM_LEVEL,
                                         0)
        self._new_member = True
        
    def _start_member(self):
        """Starts writing a new member if required.
        """
        if self._new_member:
            self._init_write(self.name)
            self._write_gzip_header()
            self._new_member = False
        
    def write(self, data):
        self._start_member()
        BaseGzipFile.write(self, data)
        
    def close(self):
        """Closes the gzip with care to handle multiple members.
        """
        if self.fileobj is None:
            return
        if self.mode == WRITE:
            self.close_member()
            self.fileobj = None
        elif self.mode == READ:
            self.fileobj = None
            
        if self.myfileobj:
            self.myfileobj.close()
            self.myfileobj = None
            
    def _read(self, size):
        # Treat end of member as end of file when _member_lock flag is set
        if self._member_lock and self._new_member:
            raise EOFError()
        else:
            return BaseGzipFile._read(self, size)
            
    def read_member(self):
        """Returns a file-like object to read one member from the gzip file.
        """
        if self._member_lock is False:
            self._member_lock = True

        if self._new_member:
            try:
                # Read one byte to move to the next member
                BaseGzipFile._read(self, 1)
                assert self._new_member is False
            except EOFError:
                return None
        
        return self

    def write_member(self, data):
        """Writes the given data as one gzip member.
        
        The data can be a string, an iterator that gives strings or a file-like object.
        """
        if isinstance(data, basestring):
            self.write(data)
        else:
            for text in data:
                self.write(text)
        self.close_member()
