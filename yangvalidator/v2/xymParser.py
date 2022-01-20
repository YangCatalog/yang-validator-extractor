# Copyright The IETF Trust 2021, All Rights Reserved
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

__author__ = 'Miroslav Kovac'
__copyright__ = 'Copyright The IETF Trust 2021, All Rights Reserved'
__license__ = 'Apache License, Version 2.0'
__email__ = 'miroslav.kovac@pantheon.tech'

import os
import sys
from datetime import datetime, timezone
from io import StringIO

from xym import __version__ as xym_version
from xym import xym


class XymParser():
    VERSION = xym_version

    def __init__(self, source, working_directory):
        if not os.path.exists(working_directory):
            os.mkdir(working_directory)
        self.__result = StringIO()
        self.__stdout = StringIO()

        # Trickery to capture stderr from the xym tools for later use
        self.__stderr_ = sys.stderr
        self.__stdout_ = sys.stdout
        sys.stderr = self.__result
        sys.stdout = self.__stdout
        self.__working_directory = working_directory
        self.__source = source

    def parse_and_extract(self):
        extracted_models = xym.xym(source_id=self.__source, dstdir=self.__working_directory, srcdir='', strict=True,
                                   strict_examples=False, debug_level=0, force_revision_regexp=True)
        xym_res = {'time': datetime.now(timezone.utc).isoformat()}
        sys.stderr = self.__stderr_
        sys.stdout = self.__stdout_
        dirname = os.path.dirname(self.__source)
        xym_res['stdout'] = self.__stdout.getvalue().replace('{}/'.format(dirname), '')
        xym_res['stderr'] = self.__result.getvalue().replace('{}/'.format(dirname), '')
        xym_res['name'] = 'xym'
        xym_res['version'] = self.VERSION
        xym_res['command'] = 'xym.xym(source_id="{}", dstdir="{}", srcdir="", strict=True, strict_examples=False,' \
                             ' debug_level=0, force_revision_regexp=True)'.format(self.__source,
                                                                                  self.__working_directory)
        return extracted_models, xym_res
