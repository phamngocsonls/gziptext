from base64 import b64decode
from .util import parse_bytes, parse_string
from .gstruct import GzipHeader, GzipFooter


ENCODING = 'latin-1'
MAX_LINE_LENGTH = 1048576  # 1MB


class Compiler:

    def compile(self, fpin, fpout):
        header = self.read_header(fpin)
        fpout.write(bytes(header))
        while True:
            line = fpin.readline(MAX_LINE_LENGTH+1)
            if len(line) > MAX_LINE_LENGTH:
                raise ValueError('line too long')
            if self.is_section_end(line):
                break
            fpout.write(b64decode(line.strip()))
        footer = self.read_footer(fpin)
        fpout.write(bytes(footer))

    def read_header(self, fp):
        header = GzipHeader()
        while True:
            line = fp.readline(MAX_LINE_LENGTH+1)
            if len(line) > MAX_LINE_LENGTH:
                raise ValueError('line too long')
            if not line:
                raise ValueError('file truncated')

            if line.startswith('#') or line.isspace():
                continue
            if self.is_section_end(line):
                break  # end of header

            i = line.find('=')
            if i < 0:
                raise ValueError('malformed config line')

            word = line[:i].strip()
            value = self.parse_value(word, line[i+1:])
            if value is not None:
                setattr(header, word, value)

        return header

    def read_footer(self, fp):
        footer = GzipFooter()

        while True:
            line = fp.readline(MAX_LINE_LENGTH+1)
            if len(line) > MAX_LINE_LENGTH:
                raise ValueError('line too long')

            if line.startswith('#') or line.isspace():
                continue
            if not line:
                break

            i = line.find('=')
            if i < 0:
                raise ValueError('malformed config line')

            word = line[:i].strip()
            value = self.parse_value(word, line[i+1:])
            setattr(footer, word, value)

        return footer

    @staticmethod
    def is_section_end(line):
        return line.startswith('--')

    @staticmethod
    def parse_value(word, buf):
        buf = buf.strip()
        if buf == '':
            return None

        if word in ('id1', 'id2', 'cm', 'ftext', 'fhcrc', 'fextra',
                    'fname', 'fcomment', 'mtime', 'xfl', 'os',
                    'extsi1', 'extsi2', 'crc16', 'isize', 'crc32'):
            return int(buf)
        elif word in ('name', 'comment'):
            return parse_string(buf).encode(ENCODING)
        elif word == 'extdata':
            return parse_bytes(buf)
        else:
            raise ValueError('unknown field: %s' % word)
