

from base64 import b64encode
from struct import unpack
from .util import crc16, parse_bytes, parse_string, wrapline
from .gstruct import GzipHeader, GzipFooter
from .format import format_header, format_footer


ENCODING = 'latin-1'
BUFFER_SIZE = 4096
MAX_STR_LENGTH = 1048576  # 1MB

class Decompiler:

    def decompile(self, fpin, fpout):
        header = GzipHeader()
        
        header = self.read_header(fpin)
        fpout.write(format_header(header))

        fpout.write('----\n')
        buf = b''
        while True:
            head = fp.read(BUFFER_SIZE)
            fpout.write(wrapline(self.decode_buffer(buf)))
            buf = head
            if len(head) < BUFFER_SIZE:
                break

        fpout.write(wrapline(self.decode_buffer(buf[:8])))
        fpout.write('----\n')

        footer = GzipFooter()
        footer.crc32 = unpack('<I', buf[-8:-4])[0]
        footer.isize = unpack('<I', buf[-4:])[0]
        fpout.write(format_footer(footer))

    def read_header(self, fp):
        hd = GzipHeader()

        hd.id1, hd.id2 = unpack('<BB', fp.read(2))
        hd.cm, flg, hd.mtime, hd.xfl, hd.os = unpack('<BBIBB', fp.read(8))
        hd.set_flg(flg)
        
        if hd.fextra:
            hd.xlen = unpack('<H', fp.read(2))[0]
            buf = fp.read(hd.xlen)
            hd.extsi1, hd.extsi2 = unpack('<BB', buf[:2])
            hd.extdata = buf[4:]
        if hd.fname:
            hd.name = self.read_string(fp)
        if hd.fcomment:
            hd.comment = self.read_string(fp)
        if hd.fhcrc:
            hd.crc16 += unpack('<H', fp.read(2))

        return hd

    @staticmethod
    def decode_buffer(buf):
        return b64encode(buf).decode()

    @staticmethod
    def read_string(fp):
        s = b''
        i = 0
        while True:
            c = fp.read(1)
            s += c
            i += 1
            if i > MAX_STR_LENGTH:
                raise ValueError('value too long')
            if not c:
                raise ValueError('header truncated')
            if c == b'\0':
                break
        return s.decode(ENCODING)
