from setuptools import setup
import os


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='bottle-yang-extractor-validator',
    version='0.3.2',
    description=(
        'A web application that allows you to fetch, extract and validate YANG modules by RFC number, by IETF draft name, or by uploading YANG files.'),
    long_description=read('README.md'),
    packages=['bottle-yang-extractor-validator'],
    author='Carl Moberg',
    author_email='camoberg@cisco.com',
    license='New-style BSD',
    url='https://github.com/cmoberg/bottle-yang-extractor-validator',
    install_requires=['xym>=0.4.4', 'pyang>=1.7.8', 'Django>=2.1.2', 'uWSGI>=2.0.18', 'certifi==2018.11.29',
                      'chardet==3.0.4', 'idna==2.8', 'lxml==4.3.2', 'pytz==2018.9', 'requests==2.21.0',
                      'urllib3==1.24.1'],
    include_package_data=True,
    keywords=['yang', 'extraction', 'validation'],
    classifiers=[]
)
