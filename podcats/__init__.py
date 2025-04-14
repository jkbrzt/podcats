"""
Podcats is a podcast feed generator and a server.

It generates RSS feeds for podcast episodes from local audio files and,
optionally, exposes the feed and as well as the episode file via
a built-in web server so that they can be imported into iTunes
or another podcast client.

"""
import datetime
import logging
import os
import re
import time
import argparse
import mimetypes
from email.utils import formatdate
from os import path
from urllib.parse import quote
from xml.sax.saxutils import escape, quoteattr

import mutagen
import humanize
from mutagen.id3 import ID3
from mutagen.mp3 import HeaderNotFoundError
from flask import Flask, Response
# noinspection PyPackageRequirements
from jinja2 import Environment, FileSystemLoader

__version__ = '0.6.3'
__licence__ = 'BSD'
__author__ = 'Jakub Roztocil'
__url__ = 'https://github.com/jakubroztocil/podcats'


WEB_PATH = '/web'
STATIC_PATH = '/static'
TEMPLATES_ROOT = os.path.join(os.path.dirname(__file__), 'templates')
BOOK_COVER_EXTENSIONS = ('.jpg', '.jpeg', '.png')

jinja2_env = Environment(loader=FileSystemLoader(TEMPLATES_ROOT))

logger = logging.getLogger(__name__)


class Episode(object):
    """Podcast episode"""

    def __init__(self, filename, relative_dir, root_url, force_order_by_name=False):
        self.filename = filename
        self.relative_dir = relative_dir
        self.root_url = root_url
        self.force_order_by_name = force_order_by_name
        self.length = os.path.getsize(filename)

        try:
            self.tags = mutagen.File(self.filename, easy=True) or {}
        except HeaderNotFoundError as err:
            self.tags = {}
            logger.warning(
                "Could not load tags of file {filename} due to: {err!r}".format(filename=self.filename, err=err)
            )

        try:
            self.id3 = ID3(self.filename)
        except Exception:
            self.id3 = None

    def __lt__(self, other):
        return self.date < other.date

    def __gt__(self, other):
        return self.date > other.date

    def __cmp__(self, other):
        a, b = self.date, other.date
        return (a > b) - (a < b)  # Python3 cmp() equivalent

    def as_xml(self):
        """Return episode item XML"""
        filename = os.path.basename(self.filename)
        directory = os.path.split(os.path.dirname(self.filename))[-1]
        template = jinja2_env.get_template('episode.xml')

        return template.render(
            title=escape(self.title),
            url=quoteattr(self.url),
            guid=escape(self.url),
            mimetype=self.mimetype,
            length=self.length,
            file_size_human=humanize.naturalsize(self.length),
            date=formatdate(self.date),
            image_url=self.image,
            duration=self.duration,
            duration_formatted=self.duration_formatted,
            filename=filename,
            directory=directory,
        )

    def as_html(self):
        """Return episode item html"""
        filename = os.path.basename(self.filename)
        directory = os.path.split(os.path.dirname(self.filename))[-1]
        template = jinja2_env.get_template('episode.html')
        try:
            date = formatdate(self.date)
        except ValueError:
            date = datetime.datetime.now(tz=datetime.timezone.utc)

        return template.render(
            title=escape(self.title),
            url=self.url,
            filename=filename,
            directory=directory,
            mimetype=self.mimetype,
            length=self.length,
            file_size_human=humanize.naturalsize(self.length),
            date=date,
            image_url=self.image,
            duration=self.duration,
            duration_formatted=self.duration_formatted,
        )

    def get_tag(self, name):
        """Return episode file tag info"""
        try:
            return self.tags[name][0]
        except (KeyError, IndexError):
            pass

    def _to_url(self, filepath):
        fn = os.path.basename(filepath)
        path_ = STATIC_PATH + '/' + self.relative_dir + '/' + fn
        path_ = re.sub(r'//', '/', path_)
        
        # Ensure we don't get double slashes when joining root_url and path
        if self.root_url.endswith('/') and path_.startswith('/'):
            path_ = path_[1:]  # Remove leading slash from path if root_url ends with slash
            
        url = self.root_url + quote(path_, errors="surrogateescape")
        return url

    @property
    def title(self):
        """Return episode title
        
        The title is constructed from:
        1. The filename (without extension) as the base title
        2. If ID3 tags are available:
           - Appends the TIT2 tag (standard ID3 title tag) if present
           - Appends the COMM tag (standard ID3 comment tag) if present
           
        This provides a fallback mechanism where the filename is always used,
        and ID3 metadata enhances the title when available.
        """
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
    def url(self):
        """Return episode url"""
        return self._to_url(self.filename)

    @property
    def date(self):
        """Return episode date as unix timestamp"""
        # If force_order_by_name is enabled, create artificial dates based on filename
        if self.force_order_by_name:
            # Extract base filename without extension
            base_name = os.path.splitext(os.path.basename(self.filename))[0]
            
            # Create a base timestamp (Jan 1, 2020)
            base_timestamp = time.mktime(time.strptime("2020-01-01", "%Y-%m-%d"))
            
            # Try to extract a number from the filename for ordering
            numbers = re.findall(r'\d+', base_name)
            if numbers:
                # Use the last number found as an offset (in seconds)
                # This creates artificial timestamps that preserve the numerical order
                offset = int(numbers[-1]) * 3600  # Convert to seconds (1 hour increments)
                return base_timestamp + offset
            else:
                # If no number in filename, use alphabetical ordering
                # Convert filename to a number based on character values
                name_value = sum(ord(c) for c in base_name)
                return base_timestamp + name_value
        
        # For regular podcast episodes, use the original logic
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
        """Return file mimetype name"""
        if self.filename.endswith('m4b'):
            return 'audio/x-m4b'
        else:
            return mimetypes.guess_type(self.filename)[0]

    @property
    def image(self):
        """Return an eventual cover image"""
        directory = os.path.split(self.filename)[0]
        image_files = []

        for fn in os.listdir(directory):
            ext = os.path.splitext(fn)[1]
            if ext.lower() in BOOK_COVER_EXTENSIONS:
                image_files.append(fn)

        if len(image_files) > 0:
            abs_path_image = os.path.join(directory, image_files[0])
            return self._to_url(abs_path_image)
        else:
            return None
            
    @property
    def duration(self):
        """Return episode duration in seconds"""
        try:
            audio = mutagen.File(self.filename)
            if audio and hasattr(audio, "info") and hasattr(audio.info, "length"):
                return int(audio.info.length)
            return None
        except Exception as err:
            logger.warning(
                "Could not get duration of file {filename} due to: {err!r}".format(
                    filename=self.filename, err=err
                )
            )
            return None
            
    @property
    def duration_formatted(self):
        """Return formatted duration as HH:MM:SS"""
        seconds = self.duration
        if seconds is None:
            return "Unknown"
        
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)
        else:
            return "{:02d}:{:02d}".format(minutes, seconds)


class Channel(object):
    """Podcast channel"""

    def __init__(self, root_dir, root_url, host, port, title, link, debug=False, force_order_by_name=False):
        self.root_dir = root_dir or os.getcwd()
        self.root_url = root_url
        self.host = host
        self.port = int(port)
        self.link = link or self.root_url
        self.title = title or os.path.basename(
            os.path.abspath(self.root_dir.rstrip('/')))
        self.description = 'Feed generated by <a href="%s">Podcats</a>.' % __url__
        self.debug = debug
        self.force_order_by_name = force_order_by_name

    def __iter__(self):
        for root, _, files in os.walk(self.root_dir):
            relative_dir = root[len(self.root_dir):]
            for fn in files:
                filepath = os.path.join(root, fn)
                mimetype = mimetypes.guess_type(filepath)[0]
                if mimetype and 'audio' in mimetype or filepath.endswith('m4b'):
                    yield Episode(filepath, relative_dir, self.root_url, self.force_order_by_name)

    def as_xml(self):
        """Return channel XML with all episode items"""
        template = jinja2_env.get_template('feed.xml')
        
        # Get all episodes and sort them
        episodes = sorted(self)
        
        # Get the first episode's image URL if available
        image_url = None
        if episodes:
            image_url = episodes[0].image
        
        return template.render(
            title=escape(self.title),
            description=escape(self.description),
            link=escape(self.link),
            image_url=image_url,
            items=u''.join(episode.as_xml() for episode in episodes)
        ).strip()

    def as_html(self):
        """Return channel HTML with all episode items"""
        template = jinja2_env.get_template('feed.html')
        return template.render(
            title=escape(self.title),
            description=self.description,
            link=escape(self.link),
            items=u''.join(episode.as_html() for episode in sorted(self)),
        ).strip().encode("utf-8", "surrogateescape")


def serve(channel):
    """Serve podcast channel and episodes over HTTP"""
    server = Flask(
        __name__,
        static_folder=channel.root_dir,
        static_url_path=STATIC_PATH,
    )
    server.route('/')(
        lambda: Response(
            channel.as_xml(),
            content_type='application/xml; charset=utf-8')
    )
    server.add_url_rule(
        WEB_PATH,
        view_func=channel.as_html,
        methods=['GET'],
    )
    server.run(host=channel.host, port=channel.port, debug=channel.debug, threaded=True)


def main():
    """Main function"""
    args = parser.parse_args()
    # Default server URL for binding and display
    url = 'http://' + args.host + ':' + args.port

    # Use public URL if provided, otherwise use server URL
    root_url = args.public_url if args.public_url else url

    channel = Channel(
        root_dir=path.abspath(args.directory),
        root_url=root_url,  # Use the public URL for links if provided
        host=args.host,     # Still use host/port for server binding
        port=args.port,
        title=args.title,
        link=args.link,
        debug=args.debug,
        force_order_by_name=args.force_order_by_name,
    )
    if args.action == 'generate':
        print(channel.as_xml())
    elif args.action == 'generate_html':
        print(channel.as_html())
    else:
        print('Welcome to the Podcats web server!')
        print('\nListening on http://{}:{}'.format(args.host, args.port))

        if args.public_url:
            print('Using public URL: {}'.format(args.public_url))

        print('\nYour podcast feed is available at:\n')
        print('\t' + channel.root_url + '\n')
        print('The web interface is available at\n')
        print('\t{url}{web_path}\n'.format(url=root_url, web_path=WEB_PATH))
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
    '--public-url',
    help='public-facing URL for links in the feed (useful when behind a reverse proxy)'
)
parser.add_argument(
    'action',
    metavar='COMMAND',
    choices=['generate', 'generate_html', 'serve'],
    help='`generate` the RSS feed to the terminal, or'
         '`serve` the generated RSS as well as audio files'
         ' via the built-in web server'
)
parser.add_argument(
    'directory',
    metavar='DIRECTORY',
    help='path to a directory with episode audio files',
)
parser.add_argument(
    '--debug',
    action="store_true",
    help='Serve with debug mode on'
)
parser.add_argument('--title', help='optional feed title')
parser.add_argument('--link', help='optional feed link')
parser.add_argument(
    '--force-order-by-name',
    action="store_true",
    help='Force ordering episodes by filename instead of by date. '
         'by creating an artificial timestamp based on the last'
         'number found in the filename.'
)


if __name__ == '__main__':
    main()
