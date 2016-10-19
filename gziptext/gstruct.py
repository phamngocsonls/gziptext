from struct import pack


class GzipHeader:

    def __init__(self):
        self.id1 = 0
        self.id2 = 0
        self.ftext = 0
        self.fhcrc = 0
        self.fextra = 0
        self.fname = 0
        self.fcomment = 0
        self.mtime = 0
        self.xfl = 0
        self.os = 255
        self.extsi1 = None
        self.extsi2 = None
        self.extdata = None
        self.name = None
        self.comment = None
        self.crc16 = None

    def __repr__(self):
        return ('<GzipHeader id1=%s, id2=%s, ftext=%s, fhcrc=%s,'
                ' fextra=%s, fname=%s, fcomment=%s, mtime=%s,'
                ' xfl=%s, os=%s, extsi1=%s, extsi2=%s,'
                ' extdata=%s, name=%s, comment=%s, crc16=%s>') % (
                self.id1, self.id2, self.ftext,  self.fhcrc,
                self.fextra, self.fname, self.fcomment, self.mtime,
                self.xfl, self.os, self.extsi1, self.extsi2,
                self.extdata, self.name, self.comment, self.crc16)

    @property
    def flg(self):
        byte = 0
        if self.ftext:
            byte |= 1
        if self.fhcrc:
            byte |= 2
        if self.fextra:
            byte |= 4
        if self.fname:
            byte |= 8
        if self.fcomment:
            byte |= 16
        return byte

    def set_flg(self, flg):
        self.ftext = int(bool(flg & 1))
        self.fhcrc = int(bool(flg & 2))
        self.fextra = int(bool(flg & 4))
        self.fname = int(bool(flg & 8))
        self.fcomment = int(bool(flg & 16))

    def __bytes__(self):
        res = b''
        res += pack('<BB', self.id1, self.id2)
        res += pack('<BBIBB', self.cm, self.flg, self.mtime, self.xfl, self.os)

        if self.fextra:
            res += pack('<H', self.xlen)
            res += pack('<BBH', self.extsi1, self.extsi2, len(self.extdata))
            res += self.extdata
        if self.fname:
            res += self.name + b'\0'
        if self.fcomment:
            res += self.comment + b'\0'
        if self.fhcrc:
            res += pack('<H', crc16(res))

        return res


class GzipFooter:

    def __init__(self):
        self.crc32 = 0
        self.isize = 0

    def __bytes__(self):
        return pack('<II', self.crc32, self.isize)
