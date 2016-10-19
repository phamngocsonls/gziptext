gziptext
========

gziptext is a "disassembler" of gzip files. This program allows you to examine
metadata of gzip binary by dumping the data in human-readable form.

Some nice things about this program:

* The resulting text dump is well annotated.
* It also supports "assembling". So you can use it to tweak metadata of your
  gzip archive.


Requirements
------------

Python 3.2 or later. (Python 2 is not supported)


Example
-------

Suppose you have a gzip file named test.gz:

    $ file test.gz
    test.gz: gzip compressed data, was "test", last modified: Sat Apr 16
    20:41:24 2016, from Unix

Dump the gzip file into the human-readable format:

    $ gziptext test.gz > test.xgz

Convert it back:

    $ gziptext -R test.xgz -o new.gz


License
-------

MIT License (See LICENSE for details)
