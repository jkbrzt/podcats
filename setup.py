import codecs

from setuptools import setup


def _get_long_description():
    with codecs.open('README.rst', encoding='utf8') as f:
        return f.read()

setup(
    name='podcats',
    version='0.5.0',
    description=('An application that generates RSS feeds for podcast '
                 'episodes from local audio files and, optionally, '
                 'exposes both via a built-in web server'),
    long_description=_get_long_description(),
    url='https://github.com/jkbrzt/podcats',
    download_url='https://github.com/jkbrzt/podcats',
    author='Jakub Roztocil',
    author_email='jakub@subtleapps.com',
    license='BSD',
    py_modules=[
        'podcats'
    ],
    entry_points={
        'console_scripts': [
            'podcats = podcats:main',
        ],
    },
    install_requires=[
        'Flask>=0.9',
        'mutagen>=1.20',
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: BSD License',
        'Topic :: Multimedia :: Sound/Audio',
    ],
)
