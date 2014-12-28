from os import path
from setuptools import setup

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst')) as f:
    readme = f.read()

setup(
    name = 'beets-follow',
    version = '1.0.0',
    description = 'Plugin for the music library manager Beets. Follow artists from your library using muspy.com',
    long_description = readme,
    url = 'https://github.com/nolsto/beets-follow',
    download_url = 'https://github.com/nolsto/beets-follow.git',
    author = 'Nolan Stover',
    author_email = 'nolan@nolsto.com',
    license = 'MIT',
    classifiers = [
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    keywords = 'beets muspy',
    packages = ['beetsplug'],
    namespace_packages = ['beetsplug'],
    install_requires = ['beets>=1.3.3'],
)
