import re
import zlib


def parse_bytes(buf):
    if not re.match('".*"$', buf):
        raise ValueError('value not quoted properly')
    return list(bytearray.fromhex(buf[1:-1]))


def parse_string(buf):
    if not re.match('".*"$', buf):
        raise ValueError('value not quoted properly')
    s = ''
    for c in buf[1:-1]:
        if c == '\\':
            continue
        s += c
    return s


def crc16(buf):
    crc32 = zlib.crc32(buf)
    return crc32 & 0xffff


def wrapline(bstr, length=72):
    """Wrap long lines."""
    res = ''
    for idx in range(0, len(bstr), length):
        res += bstr[idx:idx+length] + '\n'
    return res
