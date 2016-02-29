#!/usr/bin/env python

"""gziptext - convert gzip files into human-readable format

USAGE

    Output a gzip file as text data

        python gziptext.py < archive.gz > archive.gzt
"""

import sys
from getopt import getopt
from base64 import b64encode, b64decode
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


def to_i32(byte):
    """Decode bytes to a 32-bit integer"""
    return Struct('<H').unpack(byte)[0]


def to_i64(byte):
    """Decode bytes to a 64-bit integer"""
    return Struct('<I').unpack(byte)[0]


def from_i32(num):
    """Encode a 32-bit int to bytes"""
    return Struct('<H').pack(num)


def from_i64(num):
    """Encode a 64-bit int to bytes"""
    return Struct('<I').pack(num)


def wrapline(bstr, length=72):
    """Wrap long bytes lines"""
    res = b''
    for idx in range(0, len(bstr), length):
        res += bstr[idx:idx+length] + b'\n'
    return res


def read_gzip_header(fp):
    """Read and parse gzip header from file"""
    dic = OrderedDict()

    hd = Struct(BASE_HEADER)
    buf = saferead(fp, hd.size)
    magic, cm, flg, mtime, xfl, os = hd.unpack(buf)

    if magic != GZIP_MAGIC:
        raise BadMagicError
    if cm != 8:
        raise UnknownMethodError

    dic['cm'] = cm
    dic['flg'] = flg
    dic['mtime'] = mtime
    dic['xfl'] = xfl
    dic['os'] = os

    if dic['flg'] & FRESERVED:
        raise InvalidFlagError
    if dic['flg'] & FEXTRA:
        xlen = to_i32(saferead(fp, 2))
        dic['exfield'] = saferead(fp, xlen)
    if dic['flg'] & FNAME:
        cstr = read_cstr(fp)
        dic['name'] = cstr.decode(ENCODING)
    if dic['flg'] & FCOMMENT:
        cstr = read_cstr(fp)
        dic['comment'] = cstr.decode(ENCODING)

    return dic


def read_text_header(fp):
    dic = {}
    for bline in fp:
        bline = bline.rstrip()
        if bline == b'----':
            break
        bkey, bval = bline.split(b'\t')
        key = bkey.decode()
        if key in ('cm', 'flg', 'mtime', 'xfl', 'os'):
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

        if key in ('cm', 'flg', 'mtime', 'xfl', 'os'):
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
    return res


def to_text(fpin, fpout):
    header = read_gzip_header(fpin)
    fpout.write(create_text_header(header))

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
    header = read_text_header(fpin)
    fpout.write(create_gzip_header(header))

    for bline in fpin:
        bline = bline.rstrip()
        if bline == b'----':
            break
        fpout.write(b64decode(bline))

    footer = read_text_footer(fpin)
    fpout.write(from_i64(footer['crc32']))
    fpout.write(from_i64(footer['isize']))


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
