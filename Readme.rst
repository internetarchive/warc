warc: Python library to work with WARC files
============================================

WARC (Web ARChive) is a file format for storing web crawls.

http://www.scribd.com/doc/4303719/WARC-ISO-28500-final-draft-v018-Zentveld-080618

This `warc` library makes it very easy to work with WARC files.::

    import warc
    f = warc.open("test.warc")
    for record in f:
        print record['WARC-Target-URI'], record['Content-Length']

Documentation
-------------

The documentation of the warc library is available at http://readthedocs.org/docs/warc/en/latest/

Build Status
------------

[![Build Status](https://secure.travis-ci.org/anandology/warc.png?branch=master)](http://travis-ci.org/anandology/warc)

License
-------

This software is licensed under GPL v2. See LICENSE_ file for details.

.. LICENSE: http://github.com/anandology/warc/blob/master/LICENSE
