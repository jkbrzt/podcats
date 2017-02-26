"""
Podcats is a podcast feed generator and a server.

It generates RSS feeds for podcast episodes from local audio files and,
optionally, exposes the feed and as well as the episode file via
a built-in web server so that they can be imported into iTunes
or another podcast client.

"""
import os
import re
import time
import argparse
import mimetypes
from email.utils import formatdate
from xml.sax.saxutils import escape, quoteattr

import mutagen
from mutagen.id3 import ID3
from flask import Flask, Response


__version__ = '0.5.0'
__licence__ = 'BSD'
__author__ = 'Jakub Roztocil'
__url__ = 'https://github.com/jkbrzt/podcats'


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
    """Podcast episode"""

    def __init__(self, filename, url):
        self.filename = filename
        self.url = url
        self.tags = mutagen.File(self.filename, easy=True)
        try:
            self.id3 = ID3(self.filename)
        except:
            self.id3 = None

    def __lt__(self, other):
        return self.date < other.date

    def __gt__(self, other):
        return self.date > other.date

    def __cmp__(self, other):
        a, b = self.date, other.date
        return (a > b) - (a < b)  # Python3 cmp() equivalent

    def as_xml(self):
        """Return episode item XML."""
        return EPISODE_TEMPLATE.format(
            title=escape(self.title),
            url=quoteattr(self.url),
            quid=escape(self.url),
            mimetype=self.mimetype,
            date=formatdate(self.date)
        )

    def get_tag(self, name):
        """Return episode file tag info"""
        try:
            return self.tags[name][0]
        except (KeyError, IndexError):
            pass

    @property
    def title(self):
        """Return episode title"""
        text = os.path.splitext(os.path.basename(self.filename))[0]
        if self.id3 is not None:
            val = self.id3.getall('TIT2')
            if len(val) > 0:
                text += str(val[0])
            val = self.id3.getall('COMM')
            if len(val) > 0:
                text += ' ' + str(val[0])
        return text

    @property
    def date(self):
        """Return episode date as unix timestamp"""
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
            for fmt in formats:
                try:
                    dt = time.mktime(time.strptime(dt, fmt))
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
        """Return file mimetype name."""
        return mimetypes.guess_type(self.filename)[0]


class Channel(object):
    """Podcast channel"""

    def __init__(self, root_dir, root_url, host, port, title, link):
        self.root_dir = root_dir or os.getcwd()
        self.root_url = root_url
        self.host = host
        self.port = int(port)
        self.link = link or self.root_url
        self.title = title or os.path.basename(self.root_dir.rstrip('/'))

    def __iter__(self):
        for root, _, files in os.walk(self.root_dir):
            relative_dir = root[len(self.root_dir) + 1:]
            for fn in files:
                filepath = os.path.join(root, fn)
                mimetype = mimetypes.guess_type(filepath)[0]
                if mimetype and 'audio' in mimetype:
                    path = '/static/' + relative_dir + '/' + fn
                    path = re.sub(r'//', '/', path)
                    url = self.root_url + path
                    yield Episode(filepath, url)

    def as_xml(self):
        """Return channel XML with all episode items"""
        return FEED_TEMPLATE.format(
            title=escape(self.title),
            link=escape(self.link),
            items=u''.join(episode.as_xml() for episode in sorted(self))
        ).strip()


def serve(channel):
    """Serve podcast channel and episodes over HTTP"""
    server = Flask(
        __name__,
        static_folder=channel.root_dir,
        static_url_path='/static',
    )
    server.route('/')(
        lambda: Response(
            channel.as_xml(),
            content_type='application/xml; charset=utf-8')
    )
    server.run(host=channel.host, port=channel.port, debug=True)


def main():
    """Main function"""
    args = parser.parse_args()
    url = 'http://' + args.host + ':' + args.port
    channel = Channel(
        root_dir=args.directory,
        root_url=url,
        host=args.host,
        port=args.port,
        title=args.title,
        link=args.link,
    )
    if args.action == 'generate':
        print(channel.as_xml())
    else:
        print('Welcome to the Podcats web server!')
        print('\nYour podcast feed is available at:\n')
        print('\t' + channel.root_url + '\n')
        serve(channel)


parser = argparse.ArgumentParser(
    description='Podcats: podcast feed generator and server <%s>.' % __url__
)
parser.add_argument(
    '--host',
    default='localhost',
    help='listen hostname or IP address'
)
parser.add_argument(
    '--port',
    default='5000',
    help='listen tcp port number'
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
    help='path to a directory with episode audio files',
)
parser.add_argument('--title', help='optional feed title')
parser.add_argument('--link', help='optional feed link')


if __name__ == '__main__':
    main()
