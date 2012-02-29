.. warc documentation master file, created by
   sphinx-quickstart on Thu Feb 23 18:57:34 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

warc: Python library to work with WARC files
============================================

WARC (Web ARChive) is a file format for storing web crawls as sequences of content blocks.

The latest version of the specifications can be found at:

http://www.scribd.com/doc/4303719/WARC-ISO-28500-final-draft-v018-Zentveld-080618

This is a python library to work with files stored in WARC format.

Installation
------------

Installing warc is simple with `pip <http://www.pip-installer.org/>`_::

    $ pip install warc
	
or, with `easy_install <http://pypi.python.org/pypi/setuptools>`_::

    $ easy_install warc

Or you can get the sources by cloning the public git repository::

    git clone git://github.com/anandology/warc.git
	
and install from sources::

	$ python setup.py install

Reading a WARC File
-------------------

Reading a warc file is as simple as reading a simple file. Instead of returning lines, it returns WARC records.

::

    import warc
    f = warc.open("test.warc")
    for record in f:
        print record['WARC-Target-URI'], record['Content-Length']

The ``open`` function is a shorthand for :class:`warc.WARCFile`.::

    f = warc.WARCFile("test.warc", "rb")
    f = warc.WARCFile(fileobj=StringIO(text))

Writing WARC File
-----------------

Writing to a warc file is similar to writing to a regular file.::

    f = warc.open("test.warc", "w")
    f.write(warc_record1)
    f.write(warc_record2)
    f.close()

Working with WARC Header
------------------------

The :class:`warc.WARCHeader` object contains the list of WARC headers specified before the payload. It is just a dictionary. ::

    >>> h = warc.WARCHeader({
    ...   "WARC-Type": "response",
    ...   "WARC-Date": "2012-02-03T04:05:06Z",
    ...   "WARC-Record-ID": "<urn:uuid:80fb9262-5402-11e1-8206-545200690126>",
    ...   "Content-Length": "42"  
    ... })
    >>> 
    >>> h['WARC-Type']
    'response'
    >>> h['WARC-Record-ID']
    '<urn:uuid:80fb9262-5402-11e1-8206-545200690126>'
    >>> h['Content-Length']
    '42'

The headers are case-insensitive.
    
    >>> h['warc-type']
    'response'
    >>> h['WARC-RECORD-ID']
    '<urn:uuid:80fb9262-5402-11e1-8206-545200690126>'

The ``WARCHeader`` object is a real dictionary. 

    >>> h.keys()
    ['warc-type', 'content-length', 'warc-date', 'warc-record-id']
    >>> h.values()
    ['response', '42', '2012-02-03T04:05:06Z', '<urn:uuid:80fb9262-5402-11e1-8206-545200690126>']
    >>> h.get("Content-Type", "application/octet-stream")
    'application/octet-stream'

The commonly used headers are accessible as attributes as well.

    >>> h.type
    'response'
    >>> h.record_id
    '<urn:uuid:80fb9262-5402-11e1-8206-545200690126>'
    >>> h.content_length
    42
    >>> h.date
    "2012-02-03T04:05:06Z"
    
Note that, ``h.content_length`` is an integer where as ``h['Content-Length']`` is a string.

When a new ``WARCHeader`` object is created, the ``WARC-Record-ID``, ``WARC-Date`` and ``Content-Type`` headers can be initialized automatically.

    >>> h = warc.WARCHeader({"WARC-Type": "response"}, defaults=True)
    >>> h['WARC-Record-ID']
    '<urn:uuid:3457ee2c-5e2c-11e1-a8ff-c42c0325ac11>'
    >>> h['WARC-Date']
    '2012-02-23T14:39:34Z'
    >>> h['Content-Type']
    'application/http; msgtype=response'
    
The ``WARC-Record-ID`` is set to a UUID, ``WARC-Date`` is set to current datetime and ``Content-Type`` is initialized based on the ``WARC-Type``.

Working with WARCRecord
-----------------------

A ``WARCRecord`` can be created by passing a ``WARCHeader`` object and payload, which defaults to None when unspecified.

    >>> header = warc.WARCHeader({"WARC-Type": "response"}, defaults=True)
    >>> record = warc.WARCRecord(header, "helloworld")
    
Or by passing a dictionary of headers. ::

    >>> record = warc.WARCRecord(payload="helloworld", headers={"WARC-Type": "response"})
    
There is a handy utility to create WARCRecord from a :class:`requests.Response` object. ::

    >>> import requests
    >>> response = requests.get("http://httpbin.org/user-agent")
    >>> record = warc.WARCRecord.from_response(response)
    >>> print record
    WARC/1.0
    WARC-Type: response
    Content-Length: 201
    WARC-Date: 2012-02-23T14:58:40Z
    WARC-Target-URI: http://httpbin.org/user-agent
    Content-Type: application/http; msgtype=response
    WARC-Record-ID: <urn:uuid:def65bb4-5e2e-11e1-ad30-c42c0325ac11>

    HTTP/1.1 200 OK
    Content-Type: application/json
    Date: Thu, 23 Feb 2012 14:58:17 GMT
    Server: gunicorn/0.13.4
    Content-Length: 44
    Connection: keep-alive

    {
      "user-agent": "python-requests/0.10.1"
    }

License
-------

The warc library is licensed under the BSD 3-clause license. See LICENSE_ file for details.

.. _LICENSE: http://github.com/kennethreitz/requests/blob/master/LICENSE.rst
