Podcats
#######

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


For more options see ``podcats --help``.


Contact
=======

Jakub Roztočil

* http://github.com/jkbrzt
* http://twitter.com/jkbrzt

Changelog
=========

0.4.0 (2017-02-26)
------------------

* Fixed ``setup.py`` for Python 3 (@ymomoi)


0.3.0 (2017-02-23)
------------------

* Added Python 3 support
* Improved episode ID tag title extraction (@ymomoi)
* Replaced ``--url`` with ``--host`` and ``--port`` (@ymomoi)
