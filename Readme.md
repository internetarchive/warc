WARC
====

WARC (Web ARChive) is a file format for storing web crawls.

http://www.scribd.com/doc/4303719/WARC-ISO-28500-final-draft-v018-Zentveld-080618

This is a python library for reading and writing WARC files.

It makes read and writing WARC files very easy.

    import warc
    f = warc.open("test.warc")
    for record in f:
        print record['WARC-Target-URI'], record['Content-Length']

[Read more...](docs/index.rst).
