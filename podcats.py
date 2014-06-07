"""
Podcats is a podcast feed generator and a server.

It generates RSS feeds for podcast episodes from local audio files and,
optionally, exposes the feed and as well as the episode file via
a built-in web server so that they can be imported into iTunes
or another podcast client.

"""
import os
import time
import argparse
import mimetypes
from email.utils import formatdate
from xml.sax.saxutils import escape, quoteattr

import mutagen
from flask import Flask, Response


__version__ = '0.2.0'
__licence__ = 'BSD'
__author__ = 'Jakub Roztocil'
__email__ = 'jakub@subtleapps.com'
__url__ = 'https://github.com/jakubroztocil/podcats'


FEED_TEMPLATE = """
<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" version="2.0">
    <channel>
        <title>{title}</title>
        <link>{link}</link>
        {items}
    </channel>
</rss>
"""


EPISODE_TEMPLATE = """
    <item>
        <title>{title}</title>
        <enclosure url={url} type="{mimetype}" />
        <quid>{quid}</quid>
        <pubDate>{date}</pubDate>
    </item>
"""


class Episode(object):

    def __init__(self, filename, url):
        self.filename = filename
        self.url = url
        self.tags = mutagen.File(self.filename, easy=True)

    def __cmp__(self, other):
        return cmp(self.date, other.date)

    def as_xml(self):
        return EPISODE_TEMPLATE.format(
            title=escape(self.title),
            url=quoteattr(self.url),
            quid=escape(self.url),
            mimetype=self.mimetype,
            date=formatdate(self.date)
        )

    def get_tag(self, name):
        try:
            return self.tags[name][0]
        except (KeyError, IndexError):
            pass

    @property
    def title(self):
        return (self.get_tag('title')
                or os.path.splitext(os.path.basename(self.filename))[0])

    @property
    def date(self):
        """Return a date as unix timestamp."""
        dt = self.get_tag('date')
        if dt:
            formats = [
                '%Y-%m-%d:%H:%M:%S',
                '%Y-%m-%d:%H:%M',
                '%Y-%m-%d:%H',
                '%Y-%m-%d',
                '%Y-%m',
                '%Y',
            ]
            for format in formats:
                try:
                    dt = time.mktime(time.strptime(dt, format))
                    break
                except ValueError:
                    pass
            else:
                dt = None

        if not dt:
            dt = os.path.getmtime(self.filename)

        return dt

    @property
    def mimetype(self):
        return mimetypes.guess_type(self.filename)[0]


class Channel(object):

    def __init__(self, root_dir, root_url, title, link):
        self.root_dir = root_dir or os.getcwd()
        self.root_url = root_url
        self.link = link or self.root_url
        self.title = title or os.path.basename(self.root_dir.rstrip('/'))

    def __iter__(self):
        for root, dirs, files in os.walk(self.root_dir):
            relative_dir = root[len(self.root_dir) + 1:]
            for fn in files:
                filepath = os.path.join(root, fn)
                mimetype = mimetypes.guess_type(filepath)[0]
                if mimetype and 'audio' in mimetype:
                    url = self.root_url + relative_dir + '/' + fn
                    yield Episode(filepath, url)

    def as_xml(self):
        return FEED_TEMPLATE.format(
            title=escape(self.title),
            link=escape(self.link),
            items=u''.join(episode.as_xml() for episode in sorted(self))
        ).strip()


def serve(channel):
    server = Flask(
        __name__,
        static_folder=channel.root_dir,
        static_url_path='',
    )
    server.route('/')(
        lambda: Response(
            channel.as_xml(),
            content_type='application/xml; charset=utf8')
    )
    server.run(debug=True)


def main():
    args = parser.parse_args()
    channel = Channel(root_dir=args.directory,
                      root_url=args.url,
                      title=args.title,
                      link=args.link)
    if args.action == 'generate':
        print channel.as_xml()
    else:
        print 'Welcome to the Podcats web server!'
        print '\nYour podcast feed is available at:\n'
        print '\t' + channel.root_url
        print
        serve(channel)


parser = argparse.ArgumentParser(
    description='Podcats: podcast feed generator and server <%s>.' % __url__
)
parser.add_argument(
    '--url',
    default='http://localhost:5000/',
    help='root URL for episode files, default is http://localhost:5000/'
         ' (suitable for the built-in server)'
)
parser.add_argument(
    'action',
    metavar='COMMAND',
    choices=['generate', 'serve'],
    help='`generate` the RSS feed to the terminal, or'
         '`serve` the generated RSS as well as audio files'
         ' via the built-in web server'
)
parser.add_argument(
    'directory',
    metavar='DIRECTORY',
    help='directory with episode/audio files'
)
parser.add_argument('--title', help='optional feed title')
parser.add_argument('--link', help='optional feed link')


if __name__ == '__main__':
    main()
