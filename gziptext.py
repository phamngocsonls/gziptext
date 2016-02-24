#!/usr/bin/env python

"""gziptext - convert gzip files into human-readable format

USAGE

    Output a gzip file as text data

        python gziptext.py < archive.gz > archive.gzt
"""

import sys
from getopt import getopt
from base64 import b64encode
from struct import Struct
from collections import OrderedDict

GZIP_MAGIC = b'\x1f\x8b'
ENCODING = 'latin-1'  # RFC-1952
FTEXT = 1
FCRC16 = 2
FEXTRA = 4
FNAME = 8
FCOMMENT = 16
FRESERVED = 224

BUFF_SIZE = 4096
BASE_HEADER = '<2sBBIBB'

class GzipError(Exception): pass
class BadMagicError(GzipError): pass
class UnknownMethodError(GzipError): pass
class InvalidFlagError(GzipError): pass


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


def i32(byte):
    """Decode bytes to a 32-bit integer"""
    return Struct('<H').unpack(byte)[0]


def i64(byte):
    """Decode bytes to a 64-bit integer"""
    return Struct('<I').unpack(byte)[0]


def wrapline(bstr, length=72):
    """Wrap long bytes lines"""
    res = b''
    for idx in range(0, len(bstr), length):
        res += bstr[idx:idx+length] + b'\n'
    return res


def read_gzip_header(fp):
    """Read and parse gzip header from file"""
    data = OrderedDict()

    hd = Struct(BASE_HEADER)
    buf = saferead(fp, hd.size)
    magic, cm, flg, mtime, xfl, os = hd.unpack(buf)

    if magic != GZIP_MAGIC:
        raise BadMagicError
    if cm != 8:
        raise UnknownMethodError

    data['cm'] = cm
    data['flg'] = flg
    data['mtime'] = mtime
    data['xfl'] = xfl
    data['os'] = os

    if data['flg'] & FRESERVED:
        raise InvalidFlagError
    if data['flg'] & FEXTRA:
        xlen = i32(saferead(fp, 2))
        data['exfield'] = saferead(fp, xlen)
    if data['flg'] & FNAME:
        cstr = read_cstr(fp)
        data['name'] = cstr.decode(ENCODING)
    if data['flg'] & FCOMMENT:
        cstr = read_cstr(fp)
        data['comment'] = cstr.decode(ENCODING)

    return data


def serialize_gzip_header(dic):
    """Convert header dict to bytes"""
    res = b''
    for key, val in dic.items():
        bkey = key.encode()

        if isinstance(val, (int, str)):
            bval = str(val).encode()
        elif isinstance(val, bytes):
            bval = val
        else:
            raise ValueError
        res += bkey + b'\t' + bval + b'\n'
    return res


def usage():
    print(__doc__, file=sys.stderr)


def main():
    opts, args = getopt(sys.argv[1:], 'h', ('help',))
    for key, val in opts:
        if key in ('-h', '--help'):
            usage()
            sys.exit(0)

    stdout = sys.stdout.buffer
    stdin = sys.stdin.buffer

    header = read_gzip_header(stdin)
    stdout.write(serialize_gzip_header(header))

    prev = b''
    curr = b''
    stdout.write(b'----\n')
    while True:
        curr = stdin.read(BUFF_SIZE)
        if len(curr) < BUFF_SIZE:
            break
        stdout.write(wrapline(b64encode(prev)))
        prev = curr

    last = prev + curr
    stdout.write(wrapline(b64encode(last[:-8])))
    stdout.write(b'----\n')

    crc32 = i64(last[-8:-4])
    isize = i64(last[-4:])
    stdout.write(b'crc32\t' + str(crc32).encode() + b'\n')
    stdout.write(b'isize\t' + str(isize).encode() + b'\n')

if __name__ == '__main__':
    main()
