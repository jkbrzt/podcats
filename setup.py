from setuptools import setup


setup(
    name='podcats',
    version='0.2.0',
    description=('An application that generates RSS feeds for podcast '
                 'episodes from local audio files and, optionally, '
                 'exposes both via a built-in web server'),
    long_description=open('README.rst', encoding='utf-8').read(),
    url='https://github.com/jakubroztocil/podcats',
    download_url='https://github.com/jakubroztocil/podcats',
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
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: BSD License',
        'Topic :: Multimedia :: Sound/Audio',
    ],
)
