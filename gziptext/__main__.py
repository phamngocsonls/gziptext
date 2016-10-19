import getopt
import sys
from .compiler import Compiler
from .decompiler import Decompiler

# Constants

COMPILE = 1
DECOMPILE = 2


# Utils
def stderr(*args, **kwargs):
    kwargs['file'] = sys.stderr
    print(*args, **kwargs)


def usage():
    stderr("""\
usage: gziptext [-h] [-R] [-o output] input

OPTIONS

  -h  print help message.
  -o  specify output file path. (default: stdout)
  -R  reverse operation. convert back to gzip binary.

EXAMPLE

  $ gziptext -o example.txt example.gz
""")


if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'ho:R')
    except getopt.GetoptError as e:
        usage()
        sys.exit(1)

    action = DECOMPILE
    infile = None
    outfile = None
    for k, v in opts:
        if k == '-h':
            usage()
            sys.exit(0)
        elif k == '-o':
            outfile = v
        elif k == '-R':
            action = COMPILE

    if args:
        infile = args[0]

    if action == COMPILE:
        if infile is not None:
            infp = open(infile, 'r')
        elif not sys.stdin.isatty():
            infp = sys.stdin
        else:
            usage()
            sys.exit(1)

        if outfile is not None:
            outfp = open(outfile, 'wb')
        elif not sys.stdout.isatty():
            outfp = sys.stdout.buffer
        else:
            stderr('ERR: binary data not written to a terminal.')
            sys.exit(3)
        Compiler().compile(infp, outfp)

    elif action == DECOMPILE:
        if infile is not None:
            infp = open(infile, 'rb')
        elif not sys.stdin.isatty():
            infp = sys.stdin.buffer
        else:
            usage()
            sys.exit(1)

        if outfile is not None:
            outfp = open(outfile, 'w')
        else:
            outfp = sys.stdout
        Decompiler().decompile(infp, outfp)
    else:
        stderr('unknown mode: %s' % mode)
        sys.exit(4)
