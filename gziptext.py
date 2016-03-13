#!/usr/bin/env python3

"""gziptext - convert gzip files into human-readable format

USAGE

    Output a gzip file as text data

        python gziptext.py < archive.gz > archive.gzt
"""

import io
import sys
import zlib
import doctest
from getopt import getopt
from base64 import b64encode, b64decode
from struct import Struct
from collections import OrderedDict

GZIP_MAGIC = b'\x1f\x8b'
ENCODING = 'latin-1'  # RFC-1952
CM_DEFLATE = 8
FTEXT = 1
FHCRC = 2
FEXTRA = 4
FNAME = 8
FCOMMENT = 16
FRESERVED = 224

BUFF_SIZE = 4096
BASE_HEADER = '<2sBBIBB'
SEP = b'\t'

I8_MAX = 0xff
I16_MAX = 0xffff
I32_MAX = 0xffffffff

class GzipError(Exception): pass
class BadMagicError(GzipError): pass


def saferead(fp, size):
    """Read exactly <size> bytes from file.

    >>> saferead(io.BytesIO(b'abc'), 2)
    b'ab'
    """
    buf = fp.read(size)
    if len(buf) < size:
        raise IOError
    return buf


def read_cstr(fp):
    """Read a zero terminated string.

    >>> read_cstr(io.BytesIO(b'abc\\0'))
    b'abc'
    """
    s = b''
    while True:
        c = fp.read(1)
        if not c:
            raise IOError
        elif c == b'\0':
            break
        s += c
    return s


def to_i16(buf):
    """Decode bytes to a 16-bit integer.

    >>> to_i16(b'\\x12\\x34')
    13330
    """
    return Struct('<H').unpack(buf)[0]


def to_i32(buf):
    """Decode bytes to a 32-bit integer.

    >>> to_i32(b'\\x12\\x34\\x56\\x78')
    2018915346
    """
    return Struct('<I').unpack(buf)[0]


def from_i16(num):
    """Encode a 16-bit int to bytes.

    >>> from_i16(0x1234)
    b'4\\x12'
    """
    return Struct('<H').pack(num)


def from_i32(num):
    """Encode a 32-bit int to bytes.

    >>> from_i32(0x12345678)
    b'xV4\\x12'
    """
    return Struct('<I').pack(num)


def crc16(buf):
    """Calculate crc16 checksum of bytes.

    >>> crc16(b'abcde')
    55397
    """
    crc32 = zlib.crc32(buf)
    return crc32 & 0xffff


def is_i8(num):
    """Check if an (unsigned) 8-bit int.

    >>> is_i8(0xff)
    True
    >>> is_i8(0x100)
    False
    """
    if not isinstance(num, int):
        return False
    return 0 <= num and num <= I8_MAX


def is_i16(num):
    """Check if an (unsigned) 16-bit int.

    >>> is_i16(0xffff)
    True
    >>> is_i16(0x10000)
    False
    """
    if not isinstance(num, int):
        return False
    return 0 <= num and num <= I16_MAX


def is_i32(num):
    """Check if an (unsigned) 32-bit int.

    >>> is_i32(0xffffffff)
    True
    >>> is_i32(0x100000000)
    False
    """
    if not isinstance(num, int):
        return False
    return 0 <= num and num <= I32_MAX


def encodable(text, enc):
    """Check if a string consists of <enc> chars.

    >>> encodable('aiueo', ENCODING)
    True
    >>> encodable('\u3042', ENCODING)
    False
    """
    resp = True
    try:
        text.encode(enc)
    except UnicodeEncodeError:
        resp = False
    return resp


def wrapline(bstr, length=72):
    """Wrap long bytes lines.

    >>> wrapline(b'abcdef', length=3)
    b'abc\\ndef\\n'
    """
    res = b''
    for idx in range(0, len(bstr), length):
        res += bstr[idx:idx+length] + b'\n'
    return res


def assert_header(dic):
    """Check the consistency of a header dict"""
    assert 'cm' in dic
    assert 'flg' in dic
    assert 'mtime' in dic
    assert 'xfl' in dic
    assert 'os' in dic

    assert is_i8(dic['cm'])
    assert is_i8(dic['flg'])
    assert is_i32(dic['mtime'])
    assert is_i8(dic['xfl'])
    assert is_i8(dic['os'])

    if dic['flg'] & FEXTRA:
        assert 'exfield' in dic
        assert isinstance(dic['exfield'], bytes)
    if dic['flg'] & FNAME:
        assert 'name' in dic
        assert isinstance(dic['name'], str)
        assert encodable(dic['name'], ENCODING)
    if dic['flg'] & FCOMMENT:
        assert 'comment' in dic
        assert isinstance(dic['comment'], str)
        assert encodable(dic['comment'], ENCODING)
    if dic['flg'] & FHCRC:
        assert 'crc16' in dic
        assert is_i16(dic['crc16'])

    known_fields = {'cm', 'flg', 'mtime', 'xfl', 'os',
                    'exfield','name', 'comment', 'crc16'}
    assert known_fields.issuperset(dic.keys())

    assert dic['cm'] == CM_DEFLATE
    assert not (dic['flg'] & FRESERVED)


def read_gzip_header(fp):
    """Read and parse gzip header from file"""
    dic = OrderedDict()

    hd = Struct(BASE_HEADER)
    buf = saferead(fp, hd.size)
    magic, cm, flg, mtime, xfl, os = hd.unpack(buf)

    if magic != GZIP_MAGIC:
        raise BadMagicError

    dic['cm'] = cm
    dic['flg'] = flg
    dic['mtime'] = mtime
    dic['xfl'] = xfl
    dic['os'] = os

    if dic['flg'] & FEXTRA:
        xlen = to_i16(saferead(fp, 2))
        dic['exfield'] = saferead(fp, xlen)
    if dic['flg'] & FNAME:
        cstr = read_cstr(fp)
        dic['name'] = cstr.decode(ENCODING)
    if dic['flg'] & FCOMMENT:
        cstr = read_cstr(fp)
        dic['comment'] = cstr.decode(ENCODING)
    if dic['flg'] & FHCRC:
        dic['crc16'] = to_i16(saferead(fp, 2))

    return dic


def read_text_header(fp):
    """Parse a header dict from a file pointer"""
    dic = {}
    for bline in fp:
        bline = bline.rstrip()
        if bline == b'----':
            break
        bkey, bval = bline.split(SEP)
        key = bkey.decode()
        if key in ('cm', 'flg', 'mtime', 'xfl', 'os', 'crc16'):
            val = int(bval)
        elif key in ('name', 'comment'):
            val = bval.decode()
        elif key == 'exfield':
            val = b64decode(bval)
        else:
            raise ValueError
        dic[key] = val
    return dic


def read_text_footer(fp):
    """Parse a footer dict from a file pointer"""
    dic = {}
    for bline in fp:
        bline = bline.rstrip()
        bkey, bval = bline.split(SEP)
        key = bkey.decode()
        dic[key] = int(bval)
    return dic


def create_text_header(dic):
    """Serialize a header dict into the human-readable format"""
    res = b''
    for key, val in dic.items():
        bkey = key.encode()

        if key in ('cm', 'flg', 'mtime', 'xfl', 'os', 'crc16'):
            bval = str(val).encode()
        elif key in ('name', 'comment'):
            bval = val.encode()
        elif key == 'exfield':
            bval = b64encode(val)
        else:
            raise ValueError
        res += bkey + SEP + bval + b'\n'
    return res


def create_gzip_header(dic):
    """Serialize a header dict into bytes"""
    res = b''
    hd = Struct(BASE_HEADER)
    res += hd.pack(GZIP_MAGIC, dic['cm'], dic['flg'], dic['mtime'],
                   dic['xfl'], dic['os'])

    if dic['flg'] & FEXTRA:
        res += from_i16(len(dic['exfield']))
        res += dic['exfield']
    if dic['flg'] & FNAME:
        res += dic['name'].encode(ENCODING) + b'\0'
    if dic['flg'] & FCOMMENT:
        res += dic['comment'].encode(ENCODING) + b'\0'
    if dic['flg'] & FHCRC:
        res += from_i16(dic['crc16'])
    return res


def to_text(fpin, fpout):
    """Output a text dump of a given gzip file"""
    hdic = read_gzip_header(fpin)
    assert_header(hdic)
    fpout.write(create_text_header(hdic))

    prev = b''
    curr = b''
    fpout.write(b'----\n')
    while True:
        curr = fpin.read(BUFF_SIZE)
        if len(curr) < BUFF_SIZE:
            break
        fpout.write(wrapline(b64encode(prev)))
        prev = curr

    last = prev + curr
    fpout.write(wrapline(b64encode(last[:-8])))
    fpout.write(b'----\n')

    crc32 = to_i32(last[-8:-4])
    isize = to_i32(last[-4:])
    fpout.write(b'crc32' + SEP + str(crc32).encode() + b'\n')
    fpout.write(b'isize' + SEP + str(isize).encode() + b'\n')


def to_gzip(fpin, fpout):
    """Output a gzip binary of a given text file"""
    hdic = read_text_header(fpin)
    assert_header(hdic)
    fpout.write(create_gzip_header(hdic))

    for bline in fpin:
        bline = bline.rstrip()
        if bline == b'----':
            break
        fpout.write(b64decode(bline))

    fdic = read_text_footer(fpin)
    fpout.write(from_i32(fdic['crc32']))
    fpout.write(from_i32(fdic['isize']))


def usage():
    print(__doc__, file=sys.stderr)


def main():
    method = to_text

    opts, args = getopt(sys.argv[1:], 'hR', ('help','test'))
    for key, val in opts:
        if key in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif key == '-R':
            method = to_gzip
        elif key == '--test':
            doctest.testmod()
            sys.exit(0)

    if args:
        fpin = open(args[0], 'rb')
    else:
        fpin = sys.stdin.buffer

    fpout = sys.stdout.buffer

    method(fpin, fpout)

if __name__ == '__main__':
    main()
