warc3: Python3 library to work with WARC files
==============================================

Note: This is a fork of the original (now dead) warc repository.

WARC (Web ARChive) is a file format for storing web crawls.

http://bibnum.bnf.fr/WARC/ 

This `warc` library makes it very easy to work with WARC files.::

    import warc
    with warc.open("test.warc") as f:
        for record in f:
            print record['WARC-Target-URI'], record['Content-Length']

Documentation
-------------

The documentation of the warc library is available at http://warc.readthedocs.org/.

Apart from the install from pip, which will not work for this warc3 version, the
interface as described there is unchanged.
	
License
-------

This software is licensed under GPL v2. See LICENSE_ file for details.

.. LICENSE: http://github.com/internetarchive/warc/blob/master/LICENSE

Authors
-------

Original Python2 Versions:
  Anand Chitipothu
  Noufal Ibrahim

Python3 Port:
  Ryan Chartier 
  Jan Pieter Bruins Slot
  Almer S. Tigelaar
