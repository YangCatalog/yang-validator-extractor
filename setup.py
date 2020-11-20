# Copyright The IETF Trust 2019, All Rights Reserved
# Copyright 2015 Cisco and its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__author__ = "Miroslav Kovac, Carl Moberg"
__copyright__ = "Copyright 2015 Cisco and its affiliates, Copyright The IETF Trust 2019, All Rights Reserved"
__license__ = "Apache License, Version 2.0"
__email__ = "miroslav.kovac@pantheon.tech, camoberg@cisco.com"

import os

from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='bottle-yang-extractor-validator',
    version='0.3.2',
    description=(
        'A web application that allows you to fetch, extract and validate YANG modules by RFC number, by IETF draft name, or by uploading YANG files.'),
    long_description=read('README.md'),
    packages=['bottle-yang-extractor-validator'],
    author='Carl Moberg, Miroslav Kovac',
    author_email='camoberg@cisco.com, miroslav.kovac@pantheon.tech',
    license='New-style BSD',
    url='https://github.com/cmoberg/bottle-yang-extractor-validator',
    install_requires=requirements,
    include_package_data=True,
    keywords=['yang', 'extraction', 'validation'],
    classifiers=[]
)
