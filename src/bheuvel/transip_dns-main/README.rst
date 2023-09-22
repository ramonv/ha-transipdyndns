.. image:: https://codecov.io/gh/bheuvel/transip_dns/branch/main/graph/badge.svg?token=DF38M9OHFH
    :target: https://codecov.io/gh/bheuvel/transip_dns
.. image:: https://github.com/bheuvel/transip_dns/workflows/Python%20test/badge.svg?branch=main
.. image:: https://github.com/bheuvel/transip_dns/workflows/Upload%20Release%20Asset/badge.svg


==================
TransIP DNS (DDNS)
==================

Transip_dns is a command line tool which interfaces with the `TransIP Management API <https://api.transip.nl/rest/docs.html>`_ Besides *ordinary* record management (creation/deletion/listing), it can be used as an `DDNS <https://en.wikipedia.org/wiki/Dynamic_DNS>`_ tool to update your *home* record.


Installation
------------
Use the package manager to install transip_dns

.. code-block::

    pip install transip_dns

(Or get a copy from the `releases section of this repo <https://github.com/bheuvel/transip/releases>`_ or perform a ``python setup.py install`` from a copy of this repository.) 

Prerequisites
-------------
Obtain an `API key from TransIP <https://www.transip.nl/cp/account/api/>`_; if using for DDNS, make sure you do *not* select to accept only from ip addresses from the whitelist; if your ip has been changed it will probably not be in the whitelist and will then not allow you to use the key.

Usage
-----
Running ``transip_dns --help`` will provide useful information.

Three parameters are basically **always** required; TransIP username, private key, and the domain in question. They can be specified as:

.. code-block::

    transip_dns --user John --private_key_file /home/john/tip.key --domainname example.com --...

Or as environment variables:

.. code-block:: bash

    TID_USER=John
    TID_PRIVATE_KEY_FILE=/home/john/tip.key
    TID_DOMAINNAME=example.com

**For readability, it is assumed that in all examples, these environment variables are present**

So my initial goal was to create a DDNS script:

.. code-block:: bash

    transip_dns --record_ttl 300 --record_name homebase --query_ipv4

This will update the record, or create it if it doesn't exist.
Since record type is ``A`` by default, it's not specified. By default the script uses ``https://ipv4.icanhazip.com`` for ``A`` records.

You can check the result by listing the domain:

.. code-block:: bash

    transip_dns --list

**Reminder; the user, key and domain are read from the environment**

Deleting the record would be as simple as:

.. code-block:: bash

    transip_dns --record_name homebase

Advanced Usage
--------------
**Reminder; the user, key and domain are read from the environment**

Management of other records can be done as well. E.g updating your `SPF record <https://tools.ietf.org/html/rfc7208>`_:

.. code-block:: bash

    transip_dns --record_type TXT --record_name '@' --record_ttl 300 --record_data 'v=spf1 include:spf.example.net -all'

As a precaution, the script will not manage records with the same name, e.g. used as round-robin load balancing, or commonly used for MX records.

Docker / Kubernetes
-------------------

As all parameters can be specified as environment variables, the script can easily run within a Docker container, or even as a `CronJob in Kubernetes <https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/>`_

Creating a container would be as easy as using the following ``Dockerfile``:

.. code-block:: Docker

    FROM python:3.6
    RUN pip install transip_dns
    ENTRYPOINT [ "transip_dns" ]

Testing
-------

Both unit tests as integration tests are present. For the integration tests to work you need to provide credentials and a test domain. The integration tests will create, modify and delete record. But only the records it creates itself, and cleanup is part of the tests for record creation. Existing records should not be touched, and no test records should remain. But be sure to check the integration tests for the extremely small chance you have some of the same records. No guarantees there!

For integration testing you need to create the file ``tests/integration/_transip_credentials.py`` with you credentials (you can use/rename ``
For integration testing you need to create the file ``tests/integration/_transip_credentials.py`` with you credentials (you can use/rename ``tests/integration/_transip_credentials.py`` by removing the underscore)

As for running the tests, use tox, which will test against python version 3.6, 3.7, 3.8, 3.9 and 3.10 (if available).

For testing and development, I have used:

* `pyenv <https://github.com/pyenv/pyenv>`_ to switch and/or provide different Python versions.
* `pipenv <https://github.com/pypa/pipenv>`_ for creation of virtualenvs and dependency management
* Tests are build using `pytest <https://github.com/pytest-dev/pytest>`_
* `tox <https://tox.readthedocs.io/en/latest/>`_ for automated testing on different Python versions (Unfortunately tox was installed in site-packages, as it didn't work well within a pipenv...)

Usage of the complete tox test assumes the availability of Python versions 3.6-3.10.
Development was done using Python 3.6.

When pipenv and Python 3.6 is available, running ``make`` will create the virtualenv, run the tests and build the distribution files.

Referenced information
----------------------
* TransIP API documentation: https://api.transip.nl/rest/docs.html
* TransIP OpenAPI: https://api.transip.nl/rest/openapi.yaml
* HTTP status codes: https://tools.ietf.org/html/rfc7231#section-6
* HTTP registered status codes: https://www.iana.org/assignments/http-status-codes/http-status-codes.xhtml
* DNS record definitions: https://tools.ietf.org/html/rfc1035#section-3

License
-------

`See license file (MIT License, Copyright (c) 2020 Bob van den Heuvel) <https://github.com/bheuvel/transip/blob/main/LICENSE>`_
