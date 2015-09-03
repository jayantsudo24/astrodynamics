import re
import sys

from setuptools import setup, Command, find_packages


INIT_FILE = 'astrodynamics/__init__.py'
init_data = open(INIT_FILE).read()

AUTHORS = 'The astrodynamics developers.'
EMAIL = 'astrodynamics@frazermclean.co.uk'

metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", init_data))

VERSION = metadata['version']
LICENSE = metadata['license']
DESCRIPTION = metadata['description']

requires = []

extras_require = {
    'dev': [
        'pytest',
        'sphinx',
        'twine',
    ],
}

class PyTest(Command):
    """Allow 'python setup.py test' to run without first installing pytest"""
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import subprocess
        import sys
        errno = subprocess.call([sys.executable, 'runtests.py'])
        raise SystemExit(errno)

setup(
    name='astrodynamics',
    version=VERSION,
    description=DESCRIPTION,
    long_description=open('README.rst').read(),
    author=AUTHORS,
    author_email=EMAIL,
    url='https://github.com/python-astrodynamics/astrodynamics',
    packages=find_packages(),
    cmdclass={'test': PyTest},
    classifiers=[
        'Development Status :: 1 - Planning',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
    license=LICENSE,
    install_requires=requires,
    extras_require=extras_require)