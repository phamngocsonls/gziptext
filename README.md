gziptext
========

A simple script to dump metadata of GZIP files in JSON format.

How to install
--------------

This program is a single-file Python script with no external dependency. Thus,
what you need to do is:

 1. Install Python 3.X
 2. Copy `gziptext` to the directory under your PATH.

How to use
----------

### Basic usage

    gziptext [-h] [-v] FILE1 [FILE2..]

### Actual examples

Here is an execution example:

    $ gziptext test.txt.gz
    {"cm": 8, "crc32": 3233162706, "flg": 8, "id1": 31, "id2": 139, "isize": 11,
     "mtime": 1530146713, "name": "test.txt", "os": 3, "xfl": 0}

You can humanize the output using `-v` option:

    $ gziptext -v test.txt.gz
    {"cm": "deflate", "crc32": 3233162706, "flg": ["FNAME"], "id1": 31,
     "id2": 139, "isize": 11, "mtime": "2018-06-28 00:45:13 UTC",
     "name": "test.txt", "os": "Unix", "xfl": []}

As you can see, with this option enabled,  the 'os' field is decoded to the
name of the operating system where the file has been compressed (in this case,
it is Unix). Other fields are also decoded to be somewhat more human-readable.
