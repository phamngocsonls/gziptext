gziptext
========

gziptext is a tiny Python script to create a human-readable dump (text) of
a gzip file. It also can convert a textual dump back to a gzip binary.

Example
-------

Suppose you have a gzip file named test.gz:

    $ file test.gz
    test.gz: gzip compressed data, was "test", last modified: Sat Apr 16
    20:41:24 2016, from Unix

Dump the gzip file to the human-readable format:

    $ gziptext.py test.gz
    cm      8
    flg     8
    mtime   1460806884
    xfl     0
    os      3
    name    test
    ----
    S8wsTc3nAgA=
    ----
    crc32   4127567731
    isize   6

Modify the meta data (file name):

    $ gziptext.py test.gz  | sed 's/name\ttest/name\tedited/' \
    > | gziptext.py -R > new.gz
    $ file new.gz
    new.gz: gzip compressed data, was "edited", last modified: Sat Apr 16
    20:41:24 2016, from Unix

License
-------

MIT License (See LICENSE for details)
