gziptext
========

gziptext is a "disassembler" of gzip files. This program allows you to examine
the metadata of gzip binaries by dumping the data into human-readable format.

There are some nice things about this program:

 - Written in pure Python.
 - No external library dependency.
 - Well-annotated output.
 - Supports "assembling" (converting back to gzip binary).

Here is [an example output](doc/sample.xgz) of gziptext.


Requirements
------------

Python 3.2 or later. (Python 2 is not supported)


How to install
--------------

Install gziptext via pip:

    $ pip install git+git://github.com/fujimotos/gziptext.git


Usage
-----

Suppose you have a gzip file named test.gz:

    $ file test.gz
    test.gz: gzip compressed data, was "test", last modified: Sat Apr 16
    20:41:24 2016, from Unix

Dump the gzip file into the human-readable format:

    $ gziptext test.gz > test.xgz

Convert it back:

    $ gziptext -R test.xgz -o new.gz


NOTE
----

If you are interested in the details of gzip file format, please read
[RFC-1952](https://tools.ietf.org/html/rfc1952) (which is *extremely*
well-written).


License
-------

MIT License (See LICENSE for details)
