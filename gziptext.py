#!/usr/bin/env python

"""gziptext - convert gzip files into human-readable format

USAGE

    Output a gzip file as text data

        python gziptext.py < archive.gz > archive.gzt
"""

import sys
import zlib
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

I32_MAX = 4294967295
I64_MAX = 18446744073709551615

class GzipError(Exception): pass
class BadMagicError(GzipError): pass
class UnknownMethodError(GzipError): pass
class InvalidFlagError(GzipError): pass
class MissingFieldError(GzipError): pass
class UnknownFieldError(GzipError): pass


def saferead(fp, size):
    """Read exactly <size> bytes from file"""
    buf = fp.read(size)
    if len(buf) < size:
        raise IOError
    return buf


def read_cstr(fp):
    """Read a zero terminated string"""
    s = b''
    while True:
        c = fp.read(1)
        if not c:
            raise IOError
        elif c == b'\0':
            break
        s += c
    return s


def to_i32(buf):
    """Decode bytes to a 32-bit integer"""
    return Struct('<H').unpack(buf)[0]


def to_i64(buf):
    """Decode bytes to a 64-bit integer"""
    return Struct('<I').unpack(buf)[0]


def from_i32(num):
    """Encode a 32-bit int to bytes"""
    return Struct('<H').pack(num)


def from_i64(num):
    """Encode a 64-bit int to bytes"""
    return Struct('<I').pack(num)


def crc16(buf):
    """Calculate crc16 checksum of bytes"""
    crc32 = zlib.crc32(buf)
    return crc32 & 0xffff


def is_i32(num):
    """Check if an (unsigned) 32-bit int"""
    if not isinstance(num, int):
        return False
    return 0 <= num and num <= I32_MAX


def is_i64(num):
    """Check if an (unsigned) 64-bit int"""
    if not isinstance(num, int):
        return False
    return 0 <= num and num <= I64_MAX


def encodable(text, enc):
    resp = True
    try:
        text.encode(enc)
    except UnicodeEncodeError:
        resp = False
    return resp


def wrapline(bstr, length=72):
    """Wrap long bytes lines"""
    res = b''
    for idx in range(0, len(bstr), length):
        res += bstr[idx:idx+length] + b'\n'
    return res


def assert_header(dic):
    assert 'cm' in dic
    assert 'flg' in dic
    assert 'mtime' in dic
    assert 'xfl' in dic
    assert 'os' in dic

    assert is_i32(dic['cm'])
    assert is_i32(dic['flg'])
    assert is_i32(dic['mtime'])
    assert is_i32(dic['xfl'])
    assert is_i32(dic['os'])

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
        assert is_i32(dic['crc16'])

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
        xlen = to_i32(saferead(fp, 2))
        dic['exfield'] = saferead(fp, xlen)
    if dic['flg'] & FNAME:
        cstr = read_cstr(fp)
        dic['name'] = cstr.decode(ENCODING)
    if dic['flg'] & FCOMMENT:
        cstr = read_cstr(fp)
        dic['comment'] = cstr.decode(ENCODING)
    if dic['flg'] & FHCRC:
        dic['crc16'] = to_i32(saferead(fp, 2))

    return dic


def read_text_header(fp):
    dic = {}
    for bline in fp:
        bline = bline.rstrip()
        if bline == b'----':
            break
        bkey, bval = bline.split(b'\t')
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
    dic = {}
    for bline in fp:
        bline = bline.rstrip()
        bkey, bval = bline.split(b'\t')
        key = bkey.decode()
        dic[key] = int(bval)
    return dic


def create_text_header(dic):
    """Convert header dict to bytes"""
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
        res += bkey + b'\t' + bval + b'\n'
    return res


def create_gzip_header(dic):
    res = b''
    hd = Struct(BASE_HEADER)
    res += hd.pack(GZIP_MAGIC, dic['cm'], dic['flg'], dic['mtime'],
                   dic['xfl'], dic['os'])

    if dic['flg'] & FEXTRA:
        res += from_i32(len(dic['exfield']))
        res += dic['exfield']
    if dic['flg'] & FNAME:
        res += dic['name'].encode(ENCODING) + b'\0'
    if dic['flg'] & FCOMMENT:
        res += dic['comment'].encode(ENCODING) + b'\0'
    if dic['flg'] & FHCRC:
        res += from_i32(dic['crc16'])
    return res


def to_text(fpin, fpout):
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

    crc32 = to_i64(last[-8:-4])
    isize = to_i64(last[-4:])
    fpout.write(b'crc32\t' + str(crc32).encode() + b'\n')
    fpout.write(b'isize\t' + str(isize).encode() + b'\n')


def to_gzip(fpin, fpout):
    hdic = read_text_header(fpin)
    assert_header(hdic)
    fpout.write(create_gzip_header(hdic))

    for bline in fpin:
        bline = bline.rstrip()
        if bline == b'----':
            break
        fpout.write(b64decode(bline))

    fdic = read_text_footer(fpin)
    fpout.write(from_i64(fdic['crc32']))
    fpout.write(from_i64(fdic['isize']))


def usage():
    print(__doc__, file=sys.stderr)


def main():
    method = to_text

    opts, args = getopt(sys.argv[1:], 'hd', ('help',))
    for key, val in opts:
        if key in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif key == '-d':
            method = to_gzip

    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer

    method(stdin, stdout)

if __name__ == '__main__':
    main()
