gziptext
========

gziptext extracts meta information from GZIP files and dumps it in JSON format.

Installation
------------

 - Install Python 3.X
 - Copy `gziptext` to the directory under your PATH.

How to use
----------

Basic usage:

    gziptext FILE1 [FILE2..]

Example:

    $ gziptext compressed.gz
    {"cm": 8, "crc32": 3444995090, "flg": 0, "id1": 31, "id2": 139, "isize": 208, "mtime": 1530113163, "os": 3, "xfi": 0}
