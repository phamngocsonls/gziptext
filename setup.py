from distutils.core import setup


setup(
    name='gziptext',
    version='1.1.0',
    py_modules=['gziptext'],
    author='Fujimoto Seiji',
    author_email='fujimoto@ceptord.net',
    url='https://github.com/fujimotos/gziptext',
    description='Dump gzip metadata in human readable form',
    long_description="""\
gziptext is a "disassembler" of gzip files. This program allows you to examine
metadata of gzip binary by dumping the data in human-readable form.

Some nice things about this program:

* The resulting text dump is well annotated.
* It also supports "assembling". So you can use it to tweak metadata of your
  gzip archive.
""",
    license='MIT',
    scripts=['bin/gziptext'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: System :: Archiving :: Compression',
    ]
)
