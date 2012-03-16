warc: Python library to work with WARC files
============================================

.. image:: https://secure.travis-ci.org/anandology/warc.png?branch=master

WARC (Web ARChive) is a file format for storing web crawls.

http://bibnum.bnf.fr/WARC/

This `warc` library makes it very easy to work with WARC files.::

    import warc
    f = warc.open("test.warc")
    for record in f:
        print record['WARC-Target-URI'], record['Content-Length']

Documentation
-------------

The documentation of the warc library is available at http://readthedocs.org/docs/warc/en/latest/
	
License
-------

This software is licensed under GPL v2. See LICENSE_ file for details.

.. LICENSE: http://github.com/anandology/warc/blob/master/LICENSE
