HEADER_TEMPLATE = """\
### Identification Bytes
# The magic bytes for gzip file format.
# DO NOT modify this or the resulting file won't be recognized
# as gzip format!

id1 = {id1}
id2 = {id2}

### Compression Method
# Algorithm to use for compression. cm = 0-7 are reserved.
# cm = 8 (deflate) is the only value defined currently.

cm = {cm}

### Text Flag
# A flag value (0,1) to indicate the file is ASCII text

ftext = {ftext}

### CRC16 Flag
# A flag value (0,1) to declare CRC-16 checksum is present in
# header.

fhcrc = {fhcrc}

### Extra Field Flag
# A flag value (0,1) to declare extra fields are present in header.

fextra = {fextra}

### Name Flag
# A flag value (0,1) to declare original file name is included
# in header.

fname = {fname}

### Comment Flag
# A flag value (0,1) to declare variable-length comment text is
# present in the header.

fcomment = {fcomment}

### Modification Time
# The last modification time (seconds since the Epoch) of the original
# file. Note that this field is 32-bit length, so the maximum value is
# 4294967295 (=~ 2016-02-07).

mtime = {mtime}

### Extra Flags
# An "extra" bit flags. The meaning for each bit is depending on the
# compression method (CM) used. For deflate (CM=8), these flags are
# defined:
#
#   2: compressed with slowest method (best compression)
#   4: compressed with fastest method (least compression)

xfl = {xfl}

### Operating System
# Indicate the file system on which the compression was performed.
# Here is a list of defined values (copied from RFC1952):
#
#    0 - FAT filesystem (MS-DOS, OS/2, NT/Win32)
#    3 - Unix
#    4 - VM/CMS
#    5 - Atari TOS
#    6 - HPFS filesystem (OS/2, NT)
#    7 - Macintosh
#    8 - Z-System
#    9 - CP/M
#   10 - TOPS-20
#   11 - NTFS filesystem (NT)
#   12 - QDOS
#   13 - Acorn RISCOS
#  255 - unknown

os = {os}

### Extra Field (optional -> fextra)
# Need to set fextra to 1 to take effect.

extsi1 = {extsi2}
extsi2 = {extsi2}
extdata = {extdata}

### Name Field (optional)
# An original file name.
# Need to set fname to 1 to take effect.

name = {name}

### Comment Field (optional)
# An additional file comment.
# Need to set fcomment to 1 to take effect.

comment = {comment}

### CRC-16 (optional)
# An optional checksum for header bytes.
# Need to set fhcrc to 1 to take effect (You can safely leave this
# field unspecified. gziptext calculate the value for you if needed).

crc16 = {crc16}
"""

FOOTER_TEMPLATE = """
### CRC-32
crc32 = {crc32}

### Input Size
isize = {isize}
"""


def format_header(hd):
    dic = {}
    fields = ['id1', 'id2', 'cm', 'ftext', 'fhcrc', 'fextra', 'fname',
              'fcomment', 'mtime', 'xfl', 'os', 'extsi1', 'extsi2',
              'extdata', 'name', 'comment', 'crc16']

    for field in fields:
        val = getattr(hd, field)
        if val is None:
            dic[field] = ''
            continue

        if field in ('id1', 'id2', 'cm', 'ftext', 'fhcrc', 'fextra',
                     'fname', 'fcomment', 'mtime', 'xfl', 'os',
                     'extsi1', 'extsi2', 'crc16', 'isize', 'crc32'):
            dic[field] = str(val)
        elif field in ('name', 'comment'):
            dic[field] = '"' + val + '"'
        elif field in 'extdata':
            dic[field] = ' '.join('{:02x}'.format(val))
        else:
            raise ValueError('unknown field: %s' % field)

    return HEADER_TEMPLATE.format(**dic)


def format_footer(ft):
    return FOOTER_TEMPLATE.format(crc32=str(ft.crc32), isize=str(ft.isize))
