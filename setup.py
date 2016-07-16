from setuptools import setup
import os

def read(fname):
	return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
  name = 'bottle-yang-extractor-validator',
  version = '0.3',
  description = ('A web application that allows you to fetch, extract and validate YANG modules by RFC number, by IETF draft name, or by uploading YANG files.'),
  long_description=read('README.md'),
  packages = ['bottle-yang-extractor-validator'],
  author = 'Carl Moberg',
  author_email = 'camoberg@cisco.com',
  license = 'New-style BSD',
  url = 'https://github.com/cmoberg/bottle-yang-extractor-validator',
  install_requires = ['bottle>=0.12', 'xym>=0.2', 'CherryPy>=3.8'],
  include_package_data = True,
  keywords = ['yang', 'extraction', 'validation'],
  classifiers = [],
)
