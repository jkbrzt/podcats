Podcats
#######


.. image:: https://travis-ci.org/jakubroztocil/podcats.svg?branch=master
    :target: https://travis-ci.org/jakubroztocil/podcats


Podcats generates RSS feeds for podcast episodes from local audio files and,
optionally, exposes both the feed and episodes via a built in web server,
so that they can be conveniently imported into iTunes, Overcast or another
podcast client.


Installation
============
::

    $ pip install podcats


Usage
=====

Generate a podcast RSS from audio files stored in `my/offline/podcasts`::

    $ podcats generate my/offline/podcasts


Generate & serve the feed as well as the files at http://localhost:5000. ::

    $ podcats serve my/offline/podcasts

A web interface is available at http://localhost:5000/web.

You can also generate the html for the web interface. ::

    $ podcats generate_html my/offline/podcasts

For more options see ``podcats --help``.


Contact
=======

Jakub Roztočil

* https://github.com/jakubroztocil
* https://twitter.com/jakubroztocil
* https://roztocil.co

Changelog
=========

0.6.2 (2018-11-25)
------------------

* Fixed missing templates in PyPI package.


0.6.1 (2018-11-20)
------------------

* Find and show eventual book covers in web interface (@tiktuk)


0.6.0 (2018-11-20)
------------------

* Added a web interface (@tiktuk)
* Support m4b-files (@tiktuk)
* Added ``--debug`` flag (@tiktuk)
* Feed now validates against RSS spec (@tiktuk)


0.5.0 (2017-02-26)
------------------

* Fixed ``setup.py`` for Python 3 (@ymomoi)


0.3.0 (2017-02-23)
------------------

* Added Python 3 support
* Improved episode ID tag title extraction (@ymomoi)
* Replaced ``--url`` with ``--host`` and ``--port`` (@ymomoi)
