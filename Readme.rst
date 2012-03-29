warc: Python library to work with WARC files
============================================

.. image:: https://secure.travis-ci.org/anandology/warc.png?branch=master
   :alt: build status
   :target: http://travis-ci.org/anandology/warc

WARC (Web ARChive) is a file format for storing web crawls.

http://bibnum.bnf.fr/WARC/ 

This `warc` library makes it very easy to work with WARC files.::

    import warc
    f = warc.open("test.warc")
    for record in f:
        print record['WARC-Target-URI'], record['Content-Length']

Documentation
-------------

The documentation of the warc library is available at http://warc.readthedocs.org/.
	
License
-------

This software is licensed under GPL v2. See LICENSE_ file for details.

.. LICENSE: http://github.com/internetarchive/warc/blob/master/LICENSE
