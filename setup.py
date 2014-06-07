from setuptools import setup

import podcats


setup(
    name='podcats',
    version=podcats.__version__,
    description='',
    long_description=open('README.rst').read(),
    url='https://github.com/jakubroztocil/podcats',
    download_url='https://github.com/jakubroztocil/podcats',
    author=podcats.__author__,
    author_email=podcats.__email__,
    license=podcats.__licence__,
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
