# coding: utf-8
import os

from setuptools import setup

from tcp_udp_ping import __version__

f = open(os.path.join(os.path.dirname(__file__), 'README.md'))
readme = f.read()
f.close()

setup(
    name="tcp_udp_ping",
    version=__version__,
    description="python tool to do tcp/udp ping",
    long_description=readme,
    long_description_content_type="text/markdown",
    author='VimT',
    author_email='me@vimt.me',
    url='https://github.com/VimT/tcp-udp-ping',
    py_modules=['tcp_udp_ping'],
    entry_points={
        'console_scripts': [
            'tcp_udp_ping = tcp_udp_ping:main',
        ]
    },
    platforms=['any'],
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
)
